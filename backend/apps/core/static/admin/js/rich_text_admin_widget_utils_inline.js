/*
 * Rich Text Admin - Utilities (inline)
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    /**
     * Collects text nodes that overlap the provided range.
     *
     * @param {Range} range Selection range.
     * @returns {Node[]} Text nodes that overlap the range.
     */
    function getTextNodesInRange(range) {
        var root = range.commonAncestorContainer;
        if (root.nodeType === Node.TEXT_NODE) return [root];

        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
        var nodes = [];
        var node;
        while ((node = walker.nextNode())) {
            var nr = document.createRange();
            nr.selectNodeContents(node);
            var startsBeforeNodeEnds = range.compareBoundaryPoints(Range.START_TO_END, nr) > 0;
            var endsAfterNodeStarts = range.compareBoundaryPoints(Range.END_TO_START, nr) < 0;
            if (startsBeforeNodeEnds && endsAfterNodeStarts) nodes.push(node);
        }
        return nodes;
    }

    /**
     * Checks if the current selection is fully inside the inline tag.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {string} tagName Tag name to check.
     * @returns {boolean} True when the selection is fully inside the tag.
     */
    api.isInlineTagActive = function (editor, tagName) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return false;

        var range = sel.getRangeAt(0);
        var tagNames = api.getInlineTagAliases(tagName);

        if (range.collapsed) {
            var anc = api.findAncestor(sel.anchorNode, function (el) {
                return tagNames.indexOf(el.tagName) !== -1;
            }, editor);
            if (!anc) return false;
            return anc.textContent.replace(/\u200B/g, '').trim() !== '';
        }

        var textNodes = getTextNodesInRange(range);

        if (textNodes.length === 0) {
            return !!api.findAncestor(sel.anchorNode, function (el) {
                return tagNames.indexOf(el.tagName) !== -1;
            }, editor);
        }

        return textNodes.every(function (tn) {
            return !!api.findAncestor(tn, function (el) {
                return tagNames.indexOf(el.tagName) !== -1;
            }, editor);
        });
    };

    /**
     * Looser check for toolbar state: any part of the selection inside the tag.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {string} tagName Tag name to check.
     * @returns {boolean} True when any part overlaps the tag.
     */
    api.isInlineTagPresent = function (editor, tagName) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return false;

        var range = sel.getRangeAt(0);
        var tagNames = api.getInlineTagAliases(tagName);

        if (range.collapsed) {
            return !!api.findAncestor(sel.anchorNode, function (el) {
                return tagNames.indexOf(el.tagName) !== -1;
            }, editor);
        }

        var textNodes = getTextNodesInRange(range);
        if (textNodes.length === 0) {
            return !!api.findAncestor(sel.anchorNode, function (el) {
                return tagNames.indexOf(el.tagName) !== -1;
            }, editor);
        }

        return textNodes.some(function (tn) {
            return !!api.findAncestor(tn, function (el) {
                return tagNames.indexOf(el.tagName) !== -1;
            }, editor);
        });
    };

    /**
     * Returns the nearest inline element only when the selection is active.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {string} tagName Tag name to match.
     * @returns {Element|null} Matching inline element or null.
     */
    api.getCurrentInlineElement = function (editor, tagName) {
        if (!api.isInlineTagActive(editor, tagName)) return null;
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return null;
        var tagNames = api.getInlineTagAliases(tagName);
        return api.findAncestor(sel.anchorNode, function (el) {
            return tagNames.indexOf(el.tagName) !== -1;
        }, editor);
    };

})(window);
