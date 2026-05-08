/*
 * Rich Text Admin Widget - Actions
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    /**
     * Toggles an inline tag on the current selection.
     *
     * When the selection is fully inside the tag, the selection is unwrapped.
     * Otherwise, the selection is wrapped in the tag.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {string} tagName Tag name to toggle.
     * @param {Object} attributes Optional attributes for the wrapper.
     */
    api.toggleInlineTag = function toggleInlineTag(editor, tagName, attributes) {
        var isActive = api.isInlineTagActive(editor, tagName);
        var range    = api.getSelectionRange(editor);
        var tagNames = api.getInlineTagAliases(tagName);

        if (isActive) {
            if (!range) return;

            if (range.collapsed) {
                // Single element around caret
                var el = api.getCurrentInlineElement(editor, tagName);
                if (el) {
                    if (api.splitInlineElementAtCaret(editor, el, range)) return;
                    api.unwrapElement(el);
                }
                return;
            }

            var startMarker = document.createElement('span');
            var endMarker = document.createElement('span');
            startMarker.style.display = 'none';
            endMarker.style.display = 'none';

            var startInsert = range.cloneRange();
            var endInsert = range.cloneRange();
            startInsert.collapse(true);
            endInsert.collapse(false);
            endInsert.insertNode(endMarker);
            startInsert.insertNode(startMarker);

            var sameAncestor = api.findAncestor(startMarker, function (el) {
                return tagNames.indexOf(el.tagName) !== -1 && el.contains(endMarker);
            }, editor);

            if (sameAncestor) {
                var beforeRange = document.createRange();
                beforeRange.selectNodeContents(sameAncestor);
                beforeRange.setEndBefore(startMarker);
                var beforeFrag = beforeRange.extractContents();

                var afterRange = document.createRange();
                afterRange.selectNodeContents(sameAncestor);
                afterRange.setStartAfter(endMarker);
                var afterFrag = afterRange.extractContents();

                if (startMarker.parentNode) startMarker.parentNode.removeChild(startMarker);
                if (endMarker.parentNode) endMarker.parentNode.removeChild(endMarker);

                if (beforeFrag.childNodes.length) {
                    var beforeEl = sameAncestor.cloneNode(false);
                    beforeEl.appendChild(beforeFrag);
                    sameAncestor.parentNode.insertBefore(beforeEl, sameAncestor);
                }

                if (afterFrag.childNodes.length) {
                    var afterEl = sameAncestor.cloneNode(false);
                    afterEl.appendChild(afterFrag);
                    sameAncestor.parentNode.insertBefore(afterEl, sameAncestor.nextSibling);
                }

                api.unwrapElement(sameAncestor);
                return;
            }

            var fragment = range.extractContents();
            tagNames.forEach(function (tag) {
                var nodes = Array.prototype.slice.call(fragment.querySelectorAll(tag));
                nodes.forEach(function (el) {
                    if (el.parentNode) api.unwrapElement(el);
                });
            });
            range.insertNode(fragment);
            return;
        }

        if (!range) return;

        var element = document.createElement(tagName);
        if (attributes) {
            Object.keys(attributes).forEach(function (key) {
                element.setAttribute(key, attributes[key]);
            });
        }

        api.wrapRangeWithElement(range, element);
    };

    /**
     * Wraps the current selection in a link.
     *
     * @param {HTMLElement} editor Editor root element.
     */
    api.toggleLink = function toggleLink(editor) {
        var range = api.getSelectionRange(editor);

        if (!range || range.collapsed) {
            window.alert('Selecteer eerst tekst om een link toe te voegen.');
            return;
        }

        var href = window.prompt('Voer een URL in');
        if (!href || !href.trim()) return;

        var element = document.createElement('A');
        element.setAttribute('href', href.trim());
        api.wrapRangeWithElement(range, element);
    };

})(window);