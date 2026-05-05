/*
 * Rich Text Admin Widget - List actions
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    /**
     * Converts a list into plain paragraph blocks.
     *
     * @param {HTMLElement} listElement List element to unwrap.
     */
    api.unwrapList = function unwrapList(listElement) {
        var fragment = document.createDocumentFragment();
        Array.prototype.slice.call(listElement.children).forEach(function (item) {
            var p = document.createElement('p');
            p.innerHTML = item.innerHTML || '<br>';
            fragment.appendChild(p);
        });
        listElement.parentNode.replaceChild(fragment, listElement);
    };

    /**
     * Wraps the current block element in a new list.
     *
     * @param {HTMLElement} blockElement Block element to wrap.
     * @param {string} listTagName List tag name (UL/OL).
     */
    api.wrapCurrentBlockInList = function wrapCurrentBlockInList(blockElement, listTagName) {
        var list = document.createElement(listTagName);
        var li = document.createElement('li');
        li.innerHTML = blockElement.innerHTML || '<br>';
        list.appendChild(li);
        blockElement.parentNode.replaceChild(list, blockElement);
        api.setCaretInsideElement(li);
    };

    /**
     * Toggles list formatting for the current block.
     *
     * @param {HTMLElement} editor Editor root element.
     * @param {string} listTagName List tag name (UL/OL).
     */
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
            var sel = window.getSelection();
            if (sel && sel.rangeCount > 0) {
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

        if (currentBlock) {
            api.wrapCurrentBlockInList(currentBlock, listTagName);
        }
    };

})(window);
