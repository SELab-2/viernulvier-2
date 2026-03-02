"""
Dynamic bulk querying and execution utilities for Django admin.

Key ideas
---------
- FieldSpec + OperatorSpec define what the user can query (lookups, widgets, null handling).
- Condition forms are grouped: rows in the same group combine with AND; groups combine with OR.
- DynamicBulkService builds forms (filters + action) and executes the selected action on the filtered queryset.

How to use
----------
1) Define actions by subclassing BaseBulkAction and implement ``run(qs, cleaned_data, user)``.
2) Define field_specs with helper factories (choice_field_spec, text_field_spec, datetime_field_spec, fk_field_spec, m2m_field_spec).
3) Create a service subclass of DynamicBulkService with ``model``, ``field_specs`` and ``actions``.
4) Plug the service into admin via BulkOperationAdminMixin (see apps/core/admin_bulk.py).

Notes
-----
- M2M/FK lookups that join set ``requires_distinct=True`` to avoid duplicates.
- Empty filter rows are ignored; partially filled range rows still error.
- Operators support value kinds: single, list, range, none (is null).
"""

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from django import forms
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils.functional import cached_property


# ---------------------------------------------------------------------------
# Field specifications
# ---------------------------------------------------------------------------


@dataclass
class OperatorSpec:
    code: str
    label: str
    value_kind: str  # single, list, range, none


@dataclass
class FieldSpec:
    slug: str
    field: str
    label: str
    operators: Tuple[OperatorSpec, ...]
    form_field_factory: Callable[[str], forms.Field]
    q_builder: Callable[[str, str, object, object], Q]
    requires_distinct: bool = False


def choice_field_spec(field: str, label: str, choices, slug: Optional[str] = None, lookup_base: Optional[str] = None):
    slug = slug or field
    target = lookup_base or field

    ops = (
        OperatorSpec("eq", "=", "single"),
        OperatorSpec("ne", "!=", "single"),
        OperatorSpec("isnull", "is null", "none"),
        OperatorSpec("notnull", "is not null", "none"),
    )

    def q_builder(f, op, v1, v2):
        if op == "eq":
            return Q(**{f: v1})
        if op == "ne":
            return ~Q(**{f: v1})
        if op == "isnull":
            return Q(**{f"{f}__isnull": True})
        if op == "notnull":
            return Q(**{f"{f}__isnull": False})
        raise ValueError(op)

    return FieldSpec(
        slug=slug,
        field=target,
        label=label,
        operators=ops,
        form_field_factory=lambda name: forms.ChoiceField(
            label=label,
            choices=[("", "------")] + list(choices),
            required=False,
        ),
        q_builder=q_builder,
    )


def fk_field_spec(field: str, label: str, queryset, slug: Optional[str] = None, requires_distinct: bool = False):
    slug = slug or field

    ops = (
        OperatorSpec("eq", "=", "single"),
        OperatorSpec("ne", "!=", "single"),
        OperatorSpec("isnull", "is null", "none"),
        OperatorSpec("notnull", "is not null", "none"),
    )

    def q_builder(f, op, v1, v2):
        if op == "eq":
            return Q(**{f: v1})
        if op == "ne":
            return ~Q(**{f: v1})
        if op == "isnull":
            return Q(**{f"{f}__isnull": True})
        if op == "notnull":
            return Q(**{f"{f}__isnull": False})
        raise ValueError(op)

    return FieldSpec(
        slug=slug,
        field=field,
        label=label,
        operators=ops,
        form_field_factory=lambda name: forms.ModelChoiceField(queryset=queryset, label=label, required=False),
        q_builder=q_builder,
        requires_distinct=requires_distinct,
    )


def m2m_field_spec(field: str, label: str, queryset, slug: Optional[str] = None):
    slug = slug or field

    ops = (
        OperatorSpec("contains", "contains", "single"),
        OperatorSpec("not_contains", "not contains", "single"),
    )

    def q_builder(f, op, v1, v2):
        q = Q(**{f: v1})
        return q if op == "contains" else ~q

    return FieldSpec(
        slug=slug,
        field=field,
        label=label,
        operators=ops,
        form_field_factory=lambda name: forms.ModelChoiceField(queryset=queryset, label=label, required=False),
        q_builder=q_builder,
        requires_distinct=True,
    )


def datetime_field_spec(field: str, label: str, slug: Optional[str] = None):
    slug = slug or field

    ops = (
        OperatorSpec("gte", ">=", "single"),
        OperatorSpec("lte", "<=", "single"),
        OperatorSpec("between", "between", "range"),
        OperatorSpec("isnull", "is null", "none"),
        OperatorSpec("notnull", "is not null", "none"),
    )

    def q_builder(f, op, v1, v2):
        if op == "gte":
            return Q(**{f"{f}__gte": v1})
        if op == "lte":
            return Q(**{f"{f}__lte": v1})
        if op == "between":
            return Q(**{f"{f}__gte": v1, f"{f}__lte": v2})
        if op == "isnull":
            return Q(**{f"{f}__isnull": True})
        if op == "notnull":
            return Q(**{f"{f}__isnull": False})
        raise ValueError(op)

    return FieldSpec(
        slug=slug,
        field=field,
        label=label,
        operators=ops,
        form_field_factory=lambda name: forms.DateTimeField(label=label, required=False),
        q_builder=q_builder,
    )


def text_field_spec(field: str, label: str, slug: Optional[str] = None):
    slug = slug or field

    ops = (
        OperatorSpec("icontains", "icontains", "single"),
        OperatorSpec("contains", "contains", "single"),
        OperatorSpec("startswith", "starts with", "single"),
        OperatorSpec("istartswith", "istartswith", "single"),
        OperatorSpec("exact", "=", "single"),
        OperatorSpec("in", "in (comma)", "list"),
    )

    def q_builder(f, op, v1, v2):
        if op == "exact":
            return Q(**{f: v1})
        if op == "contains":
            return Q(**{f"{f}__contains": v1})
        if op == "icontains":
            return Q(**{f"{f}__icontains": v1})
        if op == "startswith":
            return Q(**{f"{f}__startswith": v1})
        if op == "istartswith":
            return Q(**{f"{f}__istartswith": v1})
        if op == "in":
            items = [p.strip() for p in (v1 or "").split(",") if p.strip()]
            return Q(**{f"{f}__in": items})
        raise ValueError(op)

    return FieldSpec(
        slug=slug,
        field=field,
        label=label,
        operators=ops,
        form_field_factory=lambda name: forms.CharField(label=label, required=False),
        q_builder=q_builder,
    )


# ---------------------------------------------------------------------------
# Condition formset
# ---------------------------------------------------------------------------


class ConditionForm(forms.Form):
    def __init__(self, *args, field_specs: Dict[str, FieldSpec], **kwargs):
        super().__init__(*args, **kwargs)
        self.field_specs = field_specs
        self.fields["group"] = forms.IntegerField(required=True, widget=forms.HiddenInput(), initial=0)
        self.fields["field"] = forms.ChoiceField(
            choices=[(spec.slug, spec.label) for spec in field_specs.values()],
            label="Field",
            required=True,
        )
        self.fields["operator"] = forms.ChoiceField(label="Operator", required=True)
        self.fields["value"] = forms.CharField(label="Value", required=False)
        self.fields["value2"] = forms.CharField(label="Value 2", required=False)

    def configure(self, spec: FieldSpec):
        self.fields["operator"].choices = [(op.code, op.label) for op in spec.operators]
        # Replace value fields with correct widgets (value1 & value2 share type)
        self.fields["value"] = spec.form_field_factory("value")
        self.fields["value2"] = spec.form_field_factory("value2")


def condition_formset(field_specs: Dict[str, FieldSpec], data=None):
    specs = list(field_specs.values())
    if not specs:
        raise ValueError("No field specs configured")
    total_forms = int(data.get("conditions-TOTAL_FORMS", 1)) if data else 1

    forms_list = []
    for idx in range(total_forms):
        prefix = f"conditions-{idx}"
        form = ConditionForm(data=data if data else None, prefix=prefix, field_specs=field_specs)
        selected_slug = form.data.get(f"{prefix}-field") if data else specs[0].slug
        if not data:
            form.fields["group"].initial = 0
        spec = field_specs.get(selected_slug, specs[0])
        form.configure(spec)
        forms_list.append(form)
    return forms_list


# ---------------------------------------------------------------------------
# Actions and service
# ---------------------------------------------------------------------------


@dataclass
class BulkResult:
    matched: int
    processed: int
    detail: str = ""


class BaseBulkAction:
    slug: str
    label: str
    help_text: str = ""
    form_fields: Dict[str, forms.Field] = {}

    def run(self, qs: QuerySet, cleaned_data, user) -> BulkResult:
        raise NotImplementedError


class DynamicBulkService:
    model = None
    field_specs: Iterable[FieldSpec] = ()
    actions: Iterable[BaseBulkAction] = ()

    @cached_property
    def _field_map(self) -> Dict[str, FieldSpec]:
        return {spec.slug: spec for spec in self.field_specs}

    @cached_property
    def _actions(self) -> Dict[str, BaseBulkAction]:
        return {action.slug: action for action in self.actions}

    def base_queryset(self):
        return self.model.objects.all()

    def build_forms(self, data=None, action_slug: Optional[str] = None):
        cond_forms = condition_formset(self._field_map, data=data)
        # re-configure forms after binding to ensure operator choices align with field selection
        for form in cond_forms:
            selected_slug = form.data.get(f"{form.prefix}-field") if data else form.fields["field"].initial
            spec = self._field_map.get(selected_slug) if selected_slug else None
            if spec:
                form.configure(spec)

        action = self._actions.get(action_slug)

        base_fields = {
            "action": forms.ChoiceField(
                choices=[(a.slug, a.label) for a in self.actions],
                label="Action",
                required=True,
            )
        }

        if action:
            base_fields.update(action.form_fields)

        ActionForm = type("ActionForm", (forms.Form,), base_fields)
        action_form = ActionForm(data=data if data else None)
        return action_form, cond_forms

    @transaction.atomic
    def execute(self, action_slug: str, cond_forms: List[ConditionForm], action_form: forms.Form, user):
        action = self._actions[action_slug]
        qs = self.base_queryset()

        grouped: Dict[int, List[Q]] = {}
        needs_distinct = False
        for form in cond_forms:
            if not form.is_valid():
                raise forms.ValidationError("Invalid filter")
            spec = self._field_map[form.cleaned_data["field"]]
            op = form.cleaned_data["operator"]
            v1 = form.cleaned_data.get("value")
            v2 = form.cleaned_data.get("value2")

            op_meta = next((o for o in spec.operators if o.code == op), None)
            if not op_meta:
                raise forms.ValidationError("Invalid operator")

            # Allow empty rows to be ignored (common when the user adds a row but leaves it blank)
            if op_meta.value_kind == "single":
                if v1 is None or v1 == "":
                    continue
            elif op_meta.value_kind == "range":
                if (v1 is None or v1 == "") and (v2 is None or v2 == ""):
                    continue
                if v1 is None or v1 == "" or v2 is None or v2 == "":
                    raise forms.ValidationError("Both values are required for between")
            elif op_meta.value_kind == "list":
                if v1 is None or v1 == "":
                    continue

            group_id = form.cleaned_data.get("group", 0)
            grouped.setdefault(group_id, []).append(spec.q_builder(spec.field, op, v1, v2))
            needs_distinct = needs_distinct or spec.requires_distinct

        if grouped:
            final_q = Q()
            for _, group_items in sorted(grouped.items()):
                group_q = Q()
                for q in group_items:
                    group_q &= q
                final_q |= group_q
            qs = qs.filter(final_q)

        if needs_distinct:
            qs = qs.distinct()

        return action.run(qs, action_form.cleaned_data, user)