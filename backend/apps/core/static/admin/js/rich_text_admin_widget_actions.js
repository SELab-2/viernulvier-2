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

    // Apply a block tag (H3 or P) to the current block element.
    api.formatCurrentBlock = function formatCurrentBlock(editor, tagName) {
        var currentBlock = api.getCurrentBlockElement(editor);

        if (!currentBlock) {
            currentBlock = document.createElement('p');
            currentBlock.innerHTML = editor.innerHTML || '&nbsp;';
            editor.innerHTML = '';
            editor.appendChild(currentBlock);
        }

        if (currentBlock.tagName === tagName) {
            return;
        }

        if (currentBlock.tagName === 'LI') {
            currentBlock = currentBlock.parentElement;
        }

        api.replaceElementTagName(currentBlock, tagName);
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

        if (currentList) {
            if (currentList.tagName === listTagName) {
                api.unwrapList(currentList);
            } else {
                api.replaceElementTagName(currentList, listTagName);
            }
            return;
        }

        if (!currentBlock) {
            currentBlock = document.createElement('p');
            currentBlock.innerHTML = editor.innerHTML || '&nbsp;';
            editor.innerHTML = '';
            editor.appendChild(currentBlock);
        }

        api.wrapCurrentBlockInList(currentBlock, listTagName);
    };

    // Remove formatting by replacing the selected fragment with plain text.
    api.clearFormatting = function clearFormatting(editor) {
        var selection = window.getSelection ? window.getSelection() : null;
        var range;
        var text;

        if (!selection || selection.rangeCount === 0) {
            return;
        }

        range = selection.getRangeAt(0);
        if (!editor.contains(range.commonAncestorContainer) || range.collapsed) {
            return;
        }

        // Strip the selected fragment down to plain text without depending on browser commands.
        text = range.toString();
        range.deleteContents();
        range.insertNode(document.createTextNode(text));
        api.selectNodeContents(range.endContainer.parentElement || editor);
    };
})(window);
