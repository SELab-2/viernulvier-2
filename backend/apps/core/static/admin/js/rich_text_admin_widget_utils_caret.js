/*
 * Rich Text Admin - Utilities (caret)
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    /**
     * Places the caret at the end of the given element.
     *
     * @param {Element} element Target element.
     */
    api.setCaretInsideElement = function (element) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel) return;
        var range = document.createRange();
        if (element.lastChild && element.lastChild.nodeType === Node.TEXT_NODE) {
            range.setStart(element.lastChild, element.lastChild.nodeValue.length);
        } else {
            range.selectNodeContents(element);
            range.collapse(false);
        }
        sel.removeAllRanges();
        sel.addRange(range);
    };

    /**
     * Selects the contents of a node.
     *
     * @param {Node} node Target node.
     */
    api.selectNodeContents = function (node) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel) return;
        var range = document.createRange();
        range.selectNodeContents(node);
        sel.removeAllRanges();
        sel.addRange(range);
    };

    /**
     * Computes the caret offset inside a given element.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {Element} element Element to measure within.
     * @returns {number|null} Character offset or null.
     */
    api.getCaretOffset = function (editor, element) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0 || !element) return null;
        var range = sel.getRangeAt(0);
        if (!element.contains(range.endContainer)) return null;
        var probe = range.cloneRange();
        probe.selectNodeContents(element);
        probe.setEnd(range.endContainer, range.endOffset);
        return probe.toString().length;
    };

    /**
     * Sets the caret at a specific character offset within an element.
     *
     * @param {Element} element Target element.
     * @param {number} offset Character offset.
     */
    api.setCaretAtOffset = function (element, offset) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || !element) return;
        var range = document.createRange();
        var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
        var node;
        var remaining = offset;
        while ((node = walker.nextNode())) {
            if (remaining <= node.nodeValue.length) {
                range.setStart(node, remaining);
                range.collapse(true);
                sel.removeAllRanges();
                sel.addRange(range);
                return;
            }
            remaining -= node.nodeValue.length;
        }
        api.setCaretInsideElement(element);
    };

    /**
     * Splits an inline element at the caret so formatting can be toggled.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {Element} element Inline element containing the caret.
     * @param {Range} range Current selection range.
     * @returns {boolean} True when a split occurred.
     */
    api.splitInlineElementAtCaret = function (editor, element, range) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || !range || !range.collapsed || !element) return false;
        if (!element.contains(range.startContainer)) return false;

        var elementRange = document.createRange();
        elementRange.selectNodeContents(element);
        var atStart = range.compareBoundaryPoints(Range.START_TO_START, elementRange) === 0;
        var atEnd = range.compareBoundaryPoints(Range.END_TO_END, elementRange) === 0;

        if (atStart) {
            var startRange = document.createRange();
            startRange.setStartBefore(element);
            startRange.collapse(true);
            sel.removeAllRanges();
            sel.addRange(startRange);
            return true;
        }

        if (atEnd) {
            var endRange = document.createRange();
            endRange.setStartAfter(element);
            endRange.collapse(true);
            sel.removeAllRanges();
            sel.addRange(endRange);
            return true;
        }

        var startContainer = range.startContainer;
        var offset = range.startOffset;
        var splitNode;

        if (startContainer.nodeType === Node.TEXT_NODE) {
            splitNode = startContainer.splitText(offset);
        } else {
            splitNode = document.createTextNode('');
            startContainer.insertBefore(splitNode, startContainer.childNodes[offset] || null);
        }

        var firstMoved = splitNode;
        var fragment = document.createDocumentFragment();
        var node = splitNode;
        while (node) {
            var next = node.nextSibling;
            fragment.appendChild(node);
            node = next;
        }

        if (element.parentNode) {
            element.parentNode.insertBefore(fragment, element.nextSibling);
        }

        if (element.textContent.replace(/\u200B/g, '').trim() === '') {
            api.unwrapElement(element);
        }

        if (firstMoved) {
            var caretRange = document.createRange();
            caretRange.setStart(firstMoved, 0);
            caretRange.collapse(true);
            sel.removeAllRanges();
            sel.addRange(caretRange);
        }

        return true;
    };

    /**
     * Splits an inline element at a specific range boundary.
     *
     * @param {Element} element Inline element to split.
     * @param {Range} boundaryRange Range whose start is used as split point.
     * @returns {boolean} True when a split occurred.
     */
    api.splitInlineElementAtRangeBoundary = function (element, boundaryRange) {
        if (!boundaryRange || !element) return false;
        if (!element.contains(boundaryRange.startContainer)) return false;

        var elementRange = document.createRange();
        elementRange.selectNodeContents(element);
        var atStart = boundaryRange.compareBoundaryPoints(Range.START_TO_START, elementRange) === 0;
        var atEnd = boundaryRange.compareBoundaryPoints(Range.END_TO_END, elementRange) === 0;

        if (atStart || atEnd) return false;

        var startContainer = boundaryRange.startContainer;
        var offset = boundaryRange.startOffset;
        var splitNode;

        if (startContainer.nodeType === Node.TEXT_NODE) {
            splitNode = startContainer.splitText(offset);
        } else {
            splitNode = document.createTextNode('');
            startContainer.insertBefore(splitNode, startContainer.childNodes[offset] || null);
        }

        var clone = element.cloneNode(false);
        while (splitNode) {
            var next = splitNode.nextSibling;
            clone.appendChild(splitNode);
            splitNode = next;
        }

        if (element.parentNode) {
            element.parentNode.insertBefore(clone, element.nextSibling);
        }

        return true;
    };

})(window);
