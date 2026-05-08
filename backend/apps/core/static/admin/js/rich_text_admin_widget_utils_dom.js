/*
 * Rich Text Admin - Utilities (DOM helpers)
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    /**
     * Removes empty inline elements left behind after deletions.
     *
     * @param {HTMLElement} editor Editor root element.
     */
    api.removeEmptyInlineElements = function (editor) {
        var tags = ['B', 'I', 'U', 'A', 'EM', 'STRONG'];
        tags.forEach(function (tag) {
            var els = Array.prototype.slice.call(editor.querySelectorAll(tag));
            els.forEach(function (el) {
                if (el.parentNode && el.textContent.replace(/\u200B/g, '').trim() === '') {
                    api.unwrapElement(el);
                }
            });
        });
    };

    /**
     * Replaces an element with a new tag name while keeping attributes.
     *
     * @param {Element} element Element to replace.
     * @param {string} tagName New tag name.
     * @returns {Element} Replacement element.
     */
    api.replaceElementTagName = function (element, tagName) {
        var replacement = document.createElement(tagName);
        Array.prototype.forEach.call(element.attributes, function (attr) {
            replacement.setAttribute(attr.name, attr.value);
        });
        replacement.innerHTML = element.innerHTML;
        element.parentNode.replaceChild(replacement, element);
        return replacement;
    };

    /**
     * Unwraps an element by moving its children into the parent.
     *
     * @param {Element} element Element to unwrap.
     */
    api.unwrapElement = function (element) {
        var parent = element.parentNode;
        if (!parent) return;
        while (element.firstChild) parent.insertBefore(element.firstChild, element);
        parent.removeChild(element);
    };

    /**
     * Wraps a range in a new element and updates the selection.
     *
     * @param {Range} range Selection range.
     * @param {Element} element Wrapper element.
     * @returns {Element} The wrapper element.
     */
    api.wrapRangeWithElement = function (range, element) {
        if (range.collapsed) {
            element.appendChild(document.createTextNode('\u200B'));
            range.insertNode(element);
            api.setCaretInsideElement(element);
        } else {
            element.appendChild(range.extractContents());
            range.insertNode(element);
            api.selectNodeContents(element);
        }
        return element;
    };

    /**
     * Inserts HTML at the current caret position.
     *
     * @param {string} html HTML string to insert.
     * @returns {boolean} True when insertion succeeded.
     */
    api.insertHtmlAtCursor = function (html) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return false;
        var range = sel.getRangeAt(0);
        range.deleteContents();
        var container = document.createElement('div');
        container.innerHTML = html;
        var fragment = document.createDocumentFragment();
        var lastNode = null;
        var node;
        while ((node = container.firstChild)) lastNode = fragment.appendChild(node);
        range.insertNode(fragment);
        if (lastNode) {
            range = range.cloneRange();
            range.setStartAfter(lastNode);
            range.collapse(true);
            sel.removeAllRanges();
            sel.addRange(range);
        }
        return true;
    };

    /**
     * Syncs editor HTML back to the hidden textarea.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {HTMLTextAreaElement} textarea Backing textarea.
     */
    api.syncToTextarea = function (editor, textarea) {
        var html = editor.innerHTML;
        if (
            editor.childNodes.length === 1 &&
            editor.firstChild.nodeType === 1 &&
            editor.firstChild.tagName === 'DIV'
        ) {
            var frag = document.createElement('div');
            Array.prototype.forEach.call(editor.firstChild.childNodes, function (n) {
                frag.appendChild(n.cloneNode(true));
            });
            html = frag.innerHTML;
        }
        textarea.value = html;
    };

})(window);
