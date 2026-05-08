/*
 * Rich Text Admin - Utilities (selection)
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    /**
     * Returns the current selection range within the editor, or null when
     * the selection is outside the editor.
     *
     * @param {HTMLElement} editor Editor root element.
     * @returns {Range|null} Active range inside the editor.
     */
    api.getSelectionRange = function (editor) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return null;
        if (!editor.contains(sel.anchorNode) || !editor.contains(sel.focusNode)) return null;
        return sel.getRangeAt(0);
    };

    /**
     * Walks ancestors until a matcher matches or a stop node is reached.
     *
     * @param {Node} node Starting node.
     * @param {Function} matcher Predicate for a matching ancestor.
     * @param {Node} stopNode Stop traversal at this node.
     * @returns {Element|null} Matching ancestor or null.
     */
    api.findAncestor = function (node, matcher, stopNode) {
        var cur = (node && node.nodeType === Node.TEXT_NODE) ? node.parentElement : node;
        while (cur && cur !== stopNode) {
            if (matcher(cur)) return cur;
            cur = cur.parentElement;
        }
        return null;
    };

    /**
     * Checks if a tag name is treated as a block in the editor.
     *
     * @param {string} tagName Uppercase tag name.
     * @returns {boolean} True for block tags.
     */
    api.isBlockTag = function (tagName) {
        return /^H[1-6]$/.test(tagName) || tagName === 'P' || tagName === 'LI';
    };

    /**
     * Finds the current block element that contains the caret.
     *
     * @param {HTMLElement} editor Editor root element.
     * @returns {Element|null} Block element or null.
     */
    api.getCurrentBlockElement = function (editor) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return null;
        return api.findAncestor(sel.anchorNode, function (el) {
            return el.tagName && api.isBlockTag(el.tagName);
        }, editor);
    };

    /**
     * Finds the current list element (UL/OL) that contains the caret.
     *
     * @param {HTMLElement} editor Editor root element.
     * @returns {Element|null} List element or null.
     */
    api.getCurrentListElement = function (editor) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return null;
        return api.findAncestor(sel.anchorNode, function (el) {
            return el.tagName === 'UL' || el.tagName === 'OL';
        }, editor);
    };

})(window);
