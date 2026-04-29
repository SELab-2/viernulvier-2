/*
 * Rich Text Admin - Actions
 *
 * Formatting operations for the editor (bold/italic/underline, lists, block tags).
 * These functions manipulate DOM nodes directly and rely on utils for selection
 * and caret handling.
 */
(function (root) {
    'use strict';

    // Action layer: formatting commands that operate on the editor DOM.
    // Formatting commands are grouped separately from bootstrap code so the control flow stays easier to scan.
    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    // Toggle an inline tag or wrap the current selection in it.
    api.toggleInlineTag = function toggleInlineTag(editor, tagName, attributes) {
        var currentElement = api.getCurrentInlineElement(editor, tagName);
        var range = api.getSelectionRange(editor);
        var element;

        if (currentElement) {
            api.unwrapElement(currentElement);
            return;
        }

        if (!range) {
            return;
        }

        element = document.createElement(tagName);
        if (attributes) {
            Object.keys(attributes).forEach(function (key) {
                element.setAttribute(key, attributes[key]);
            });
        }

        api.wrapRangeWithElement(range, element);
    };

    // Create or update a link around the current selection.
    api.toggleLink = function toggleLink(editor) {
        var href = window.prompt('Enter URL');

        if (!href) {
            return;
        }

        api.toggleInlineTag(editor, 'A', { href: href });
    };

    // Apply a block tag (H2/H3/H4 or P) to the current block element.
    api.formatCurrentBlock = function formatCurrentBlock(editor, tagName) {
        var currentBlock = api.getCurrentBlockElement(editor);
        var selection = window.getSelection ? window.getSelection() : null;
        var range;
        var caretOffset = null;
        var replacement;

        if (!currentBlock) {
            if (!selection || selection.rangeCount === 0) {
                return;
            }

            range = selection.getRangeAt(0);
            if (!editor.contains(range.commonAncestorContainer)) {
                return;
            }

            currentBlock = document.createElement('p');

            if (range.collapsed) {
                currentBlock.innerHTML = '&nbsp;';
                range.insertNode(currentBlock);
            } else {
                var content = range.extractContents();
                currentBlock.appendChild(content);
                range.insertNode(currentBlock);
            }

            api.setCaretInsideElement(currentBlock);
        }

        if (currentBlock.tagName === tagName) {
            return;
        }

        if (currentBlock.tagName === 'LI') {
            currentBlock = currentBlock.parentElement;
        }

        caretOffset = api.getCaretOffset(editor, currentBlock);
        replacement = api.replaceElementTagName(currentBlock, tagName);

        if (caretOffset !== null) {
            api.setCaretAtOffset(replacement, caretOffset);
        } else {
            api.setCaretInsideElement(replacement);
        }
    };

    // Convert list items back into paragraphs.
    api.unwrapList = function unwrapList(listElement) {
        var fragment = document.createDocumentFragment();
        var items = Array.prototype.slice.call(listElement.children);

        items.forEach(function (item) {
            var paragraph = document.createElement('p');

            paragraph.innerHTML = item.innerHTML || '<br>';
            fragment.appendChild(paragraph);
        });

        listElement.parentNode.replaceChild(fragment, listElement);
    };

    // Replace the current block with a list wrapper.
    api.wrapCurrentBlockInList = function wrapCurrentBlockInList(blockElement, listTagName) {
        var list = document.createElement(listTagName);
        var listItem = document.createElement('li');

        listItem.innerHTML = blockElement.innerHTML || '<br>';
        list.appendChild(listItem);
        blockElement.parentNode.replaceChild(list, blockElement);
        api.setCaretInsideElement(listItem);
    };

    // Toggle list state for the current block.
    api.toggleList = function toggleList(editor, listTagName) {
        var currentList = api.getCurrentListElement(editor);
        var currentBlock = api.getCurrentBlockElement(editor);

        // If we are already in a list: either unwrap or change type
        if (currentList) {
            if (currentList.tagName === listTagName) {
                api.unwrapList(currentList);
            } else {
                api.replaceElementTagName(currentList, listTagName);
            }
            return;
        }

        // If we don't have a block element at the cursor position, we need to create one to wrap in a list.
        if (!currentBlock) {
            var sel = window.getSelection();
            if (sel.rangeCount > 0) {
                var range = sel.getRangeAt(0);
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

        // If we have a block element at the cursor position, wrap it in a list.
        if (currentBlock) {
            api.wrapCurrentBlockInList(currentBlock, listTagName);
        }
    };

})(window);
