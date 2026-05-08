/*
 * Rich Text Admin Widget - Block actions
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    /**
     * Changes the current block element to the desired tag.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {string} tagName Target tag name.
     */
    api.formatCurrentBlock = function formatCurrentBlock(editor, tagName) {
        var currentBlock = api.getCurrentBlockElement(editor);
        var selection = window.getSelection ? window.getSelection() : null;
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

})(window);
