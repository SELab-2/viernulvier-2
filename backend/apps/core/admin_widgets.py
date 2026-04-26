"""Reusable custom admin widgets and decorators."""

from collections.abc import Callable
from typing import Any

from django import forms
from django.utils.safestring import mark_safe


RICH_TEXT_BOOTSTRAP_SCRIPT = """
<script>
    (function () {
        if (!window.__richTextAdminBootstrap) {
            window.__richTextAdminBootstrap = true;

            window.__richTextAdminInit = function (root) {
                var STYLE_ID = 'richtext-admin-widget-style';
                if (!document.getElementById(STYLE_ID)) {
                    var style = document.createElement('style');
                    style.id = STYLE_ID;
                    style.textContent = [
                        '.richtext-admin-wrapper { border: 1px solid #d0d7de; border-radius: 6px; background: #fff; width: 100%; max-width: 920px; box-sizing: border-box; }',
                        '.richtext-admin-toolbar { display: flex; flex-wrap: wrap; gap: 4px; padding: 6px; border-bottom: 1px solid #e5e7eb; background: #f8fafc; }',
                        '.richtext-admin-toolbar button { border: 1px solid #d1d5db; background: #fff; border-radius: 4px; padding: 3px 8px; cursor: pointer; font-size: 12px; }',
                        '.richtext-admin-toolbar button:hover { background: #f3f4f6; }',
                        '.richtext-admin-toolbar button.is-active { background: #dbeafe; border-color: #60a5fa; color: #1e3a8a; }',
                        '.richtext-admin-editor { min-height: 180px; max-height: 460px; overflow: auto; padding: 10px; line-height: 1.5; width: 100%; box-sizing: border-box; }',
                        '.richtext-admin-editor ul { list-style: disc !important; list-style-position: outside !important; margin: 0.5em 0 0.5em 1.5em !important; padding-left: 0.5em !important; }',
                        '.richtext-admin-editor ol { list-style: decimal !important; list-style-position: outside !important; margin: 0.5em 0 0.5em 1.5em !important; padding-left: 0.5em !important; }',
                        '.richtext-admin-editor li { display: list-item !important; margin: 0.2em 0 !important; }',
                        '.richtext-admin-editor:focus { outline: 2px solid #79aec8; outline-offset: -2px; }',
                        '.richtext-admin-input { width: 100%; box-sizing: border-box; }'
                    ].join('');
                    document.head.appendChild(style);
                }

                function runCommand(command, commandValue) {
                    if (typeof document.execCommand === 'function') {
                        document.execCommand(command, false, commandValue || null);
                    }
                }

                function createToolbarButton(label, title, onClick, commandName) {
                    var button = document.createElement('button');
                    button.type = 'button';
                    button.textContent = label;
                    button.title = title;
                    if (commandName) {
                        button.dataset.command = commandName;
                        button.setAttribute('aria-pressed', 'false');
                    }
                    // Keep editor selection when clicking toolbar controls.
                    button.addEventListener('mousedown', function (event) {
                        event.preventDefault();
                    });
                    button.addEventListener('click', function () {
                        onClick();
                    });
                    return button;
                }

                function updateToolbarState(toolbar) {
                    if (!toolbar || typeof document.queryCommandState !== 'function') {
                        return;
                    }

                    toolbar.querySelectorAll('button[data-command]').forEach(function (button) {
                        var command = button.dataset.command;
                        var isActive = false;

                        try {
                            isActive = !!document.queryCommandState(command);
                        } catch (error) {
                            isActive = false;
                        }

                        button.classList.toggle('is-active', isActive);
                        button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
                    });
                }

                function syncToTextarea(editor, textarea) {
                    textarea.value = editor.innerHTML;
                }

                function initTextarea(textarea) {
                    if (!textarea || textarea.dataset.richtextInitialized === '1') {
                        return;
                    }

                    textarea.dataset.richtextInitialized = '1';

                    var wrapper = document.createElement('div');
                    wrapper.className = 'richtext-admin-wrapper';

                    var toolbar = document.createElement('div');
                    toolbar.className = 'richtext-admin-toolbar';

                    function applyCommand(command, commandValue) {
                        runCommand(command, commandValue);
                        editor.focus();
                        syncToTextarea(editor, textarea);
                        updateToolbarState(toolbar);
                    }

                    toolbar.appendChild(createToolbarButton('B', 'Bold', function () { applyCommand('bold'); }, 'bold'));
                    toolbar.appendChild(createToolbarButton('I', 'Italic', function () { applyCommand('italic'); }, 'italic'));
                    toolbar.appendChild(createToolbarButton('U', 'Underline', function () { applyCommand('underline'); }, 'underline'));
                    toolbar.appendChild(createToolbarButton('H3', 'Heading', function () { applyCommand('formatBlock', 'h3'); }));
                    toolbar.appendChild(createToolbarButton('P', 'Paragraph', function () { applyCommand('formatBlock', 'p'); }));
                    toolbar.appendChild(createToolbarButton('UL', 'Bullet list', function () { applyCommand('insertUnorderedList'); }, 'insertUnorderedList'));
                    toolbar.appendChild(createToolbarButton('OL', 'Numbered list', function () { applyCommand('insertOrderedList'); }, 'insertOrderedList'));
                    toolbar.appendChild(createToolbarButton('Link', 'Insert link', function () {
                        var link = window.prompt('Enter URL');
                        if (link) {
                            applyCommand('createLink', link);
                        }
                    }));
                    toolbar.appendChild(createToolbarButton('Clean', 'Remove formatting', function () { applyCommand('removeFormat'); }));

                    var editor = document.createElement('div');
                    editor.className = 'richtext-admin-editor';
                    editor.contentEditable = 'true';
                    editor.innerHTML = textarea.value || '';

                    editor.addEventListener('input', function () { syncToTextarea(editor, textarea); });
                    editor.addEventListener('blur', function () { syncToTextarea(editor, textarea); });

                    wrapper.appendChild(toolbar);
                    wrapper.appendChild(editor);

                    textarea.style.display = 'none';
                    textarea.parentNode.insertBefore(wrapper, textarea);

                    var form = textarea.closest('form');
                    if (form) {
                        form.addEventListener('submit', function () {
                            syncToTextarea(editor, textarea);
                        });
                    }

                    editor.addEventListener('keyup', function () {
                        updateToolbarState(toolbar);
                    });

                    editor.addEventListener('mouseup', function () {
                        updateToolbarState(toolbar);
                    });

                    editor.addEventListener('focus', function () {
                        updateToolbarState(toolbar);
                    });

                    document.addEventListener('selectionchange', function () {
                        if (document.activeElement === editor || editor.contains(document.activeElement)) {
                            updateToolbarState(toolbar);
                        }
                    });

                    updateToolbarState(toolbar);
                }

                var scope = root || document;
                var textareas = scope.querySelectorAll('textarea[data-richtext-editor="1"]');
                textareas.forEach(initTextarea);
            };

            if (document.body) {
                var observer = new MutationObserver(function (mutations) {
                    mutations.forEach(function (mutation) {
                        mutation.addedNodes.forEach(function (node) {
                            if (!node || node.nodeType !== 1 || !window.__richTextAdminInit) {
                                return;
                            }
                            if (node.matches && node.matches('textarea[data-richtext-editor="1"]')) {
                                window.__richTextAdminInit(node.parentNode || document);
                                return;
                            }
                            if (node.querySelectorAll) {
                                window.__richTextAdminInit(node);
                            }
                        });
                    });
                });

                observer.observe(document.body, { childList: true, subtree: true });
            }
        }

        if (window.__richTextAdminInit) {
            window.__richTextAdminInit(document);
        }
    })();
</script>
"""


class RichTextAdminWidget(forms.Textarea):
        """Simple WYSIWYG textarea widget for HTML-capable admin fields."""

        def __init__(self, attrs: dict[str, Any] | None = None):
                base_attrs = {
                        "data-richtext-editor": "1",
                        "class": "vLargeTextField richtext-admin-input",
                }
                if attrs:
                        base_attrs.update(attrs)
                super().__init__(attrs=base_attrs)

        def render(self, name: str, value: Any, attrs: dict[str, Any] | None = None, renderer: Any = None) -> str:
                textarea_html = super().render(name, value, attrs=attrs, renderer=renderer)
                return mark_safe(f"{textarea_html}{RICH_TEXT_BOOTSTRAP_SCRIPT}")


def enable_rich_text_for_fields(
    *field_names: str,
    widget_attrs: dict[str, Any] | None = None,
    help_text_suffix: str = "",
) -> Callable[[type], type]:
    """Class decorator that enables the rich text widget for selected fields.

    Example:
        @enable_rich_text_for_fields("body", "excerpt")
        class BlogTranslationInline(admin.TabularInline):
            ...
    """

    configured_fields = frozenset(field_names)
    configured_widget_attrs = dict(widget_attrs or {})

    def decorator(admin_class: type) -> type:
        original_formfield_for_dbfield = admin_class.__dict__.get("formfield_for_dbfield")

        def formfield_for_dbfield(self: Any, db_field: Any, request: Any, **kwargs: Any) -> Any:
            if db_field.name in self.rich_text_fields:
                kwargs.setdefault(
                    "widget",
                    RichTextAdminWidget(attrs=self.rich_text_widget_attrs),
                )

            if original_formfield_for_dbfield is not None:
                formfield = original_formfield_for_dbfield(self, db_field, request, **kwargs)
            else:
                formfield = super(admin_class, self).formfield_for_dbfield(db_field, request, **kwargs)

            if formfield is not None and db_field.name in self.rich_text_fields:
                existing_help_text = formfield.help_text or ""
                if self.rich_text_help_text_suffix and self.rich_text_help_text_suffix not in existing_help_text:
                    if existing_help_text:
                        formfield.help_text = f"{existing_help_text} {self.rich_text_help_text_suffix}"
                    else:
                        formfield.help_text = self.rich_text_help_text_suffix

            return formfield

        admin_class.rich_text_fields = configured_fields
        admin_class.rich_text_widget_attrs = configured_widget_attrs
        admin_class.rich_text_help_text_suffix = help_text_suffix
        admin_class.formfield_for_dbfield = formfield_for_dbfield
        return admin_class

    return decorator
