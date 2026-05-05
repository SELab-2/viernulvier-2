/*
 * Rich Text Admin - Actions (rewrite)
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    /*
     * toggleInlineTag
     *
     * If the whole selection is already wrapped in tagName → unwrap all
     * matching elements that overlap the selection.
     * Otherwise → wrap the selection.
     *
     * This handles every case:
     *   • Collapsed caret inside <b>  → unwrap that single <b>
     *   • Selection fully inside one <b>  → unwrap that <b>
     *   • Selection spanning multiple <b>foo</b> <b>bar</b>  → unwrap both
     *   • Selection not yet bold  → wrap in new <b>
     */
    api.toggleInlineTag = function toggleInlineTag(editor, tagName, attributes) {
        var isActive = api.isInlineTagActive(editor, tagName);
        var range    = api.getSelectionRange(editor);
        var tagNames = api.getInlineTagAliases(tagName);

        if (isActive) {
            /* ── Unwrap ─────────────────────────────────────────────────── */
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

        /* ── Wrap ───────────────────────────────────────────────────────── */
        if (!range) return;

        var element = document.createElement(tagName);
        if (attributes) {
            Object.keys(attributes).forEach(function (key) {
                element.setAttribute(key, attributes[key]);
            });
        }

        api.wrapRangeWithElement(range, element);
    };

    /*
     * toggleLink
     *
     * Requires a non-collapsed selection. Shows a friendly alert when the user
     * forgot to select text first. Never toggles / removes links.
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

    /* ------------------------------------------------------------------ */
    /* Block formatting                                                     */
    /* ------------------------------------------------------------------ */
    api.formatCurrentBlock = function formatCurrentBlock(editor, tagName) {
        var currentBlock = api.getCurrentBlockElement(editor);
        var selection    = window.getSelection ? window.getSelection() : null;
        var range, caretOffset, replacement;

        if (!currentBlock) {
            if (!selection || selection.rangeCount === 0) return;
            range = selection.getRangeAt(0);
            if (!editor.contains(range.commonAncestorContainer)) return;

            currentBlock = document.createElement('p');
            if (range.collapsed) {
                currentBlock.innerHTML = '&nbsp;';
                range.insertNode(currentBlock);
            } else {
                currentBlock.appendChild(range.extractContents());
                range.insertNode(currentBlock);
            }
            api.setCaretInsideElement(currentBlock);
        }

        if (currentBlock.tagName === tagName) return;
        if (currentBlock.tagName === 'LI') currentBlock = currentBlock.parentElement;

        caretOffset = api.getCaretOffset(editor, currentBlock);
        replacement = api.replaceElementTagName(currentBlock, tagName);

        if (caretOffset !== null) {
            api.setCaretAtOffset(replacement, caretOffset);
        } else {
            api.setCaretInsideElement(replacement);
        }
    };

    /* ------------------------------------------------------------------ */
    /* List helpers                                                         */
    /* ------------------------------------------------------------------ */
    api.unwrapList = function unwrapList(listElement) {
        var fragment = document.createDocumentFragment();
        Array.prototype.slice.call(listElement.children).forEach(function (item) {
            var p = document.createElement('p');
            p.innerHTML = item.innerHTML || '<br>';
            fragment.appendChild(p);
        });
        listElement.parentNode.replaceChild(fragment, listElement);
    };

    api.wrapCurrentBlockInList = function wrapCurrentBlockInList(blockElement, listTagName) {
        var list = document.createElement(listTagName);
        var li   = document.createElement('li');
        li.innerHTML = blockElement.innerHTML || '<br>';
        list.appendChild(li);
        blockElement.parentNode.replaceChild(list, blockElement);
        api.setCaretInsideElement(li);
    };

    api.toggleList = function toggleList(editor, listTagName) {
        var currentList  = api.getCurrentListElement(editor);
        var currentBlock = api.getCurrentBlockElement(editor);

        if (currentList) {
            if (currentList.tagName === listTagName) {
                api.unwrapList(currentList);
            } else {
                api.replaceElementTagName(currentList, listTagName);
            }
            return;
        }

        if (!currentBlock) {
            var sel = window.getSelection();
            if (sel && sel.rangeCount > 0) {
                var range    = sel.getRangeAt(0);
                currentBlock = document.createElement('p');
                if (range.collapsed) {
                    currentBlock.innerHTML = '<br>';
                    range.insertNode(currentBlock);
                } else {
                    currentBlock.appendChild(range.extractContents());
                    range.insertNode(currentBlock);
                }
            }
        }

        if (currentBlock) {
            api.wrapCurrentBlockInList(currentBlock, listTagName);
        }
    };

})(window);