/*
 * Rich Text Admin - Utilities
 */
(function (root) {
    'use strict';

    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    api.STYLE_ID  = 'richtext-admin-widget-style';
    api.SELECTOR  = 'textarea[data-richtext-editor="1"]';

    // Styles
    // This is required to overwrite the styles forced by django cms
    api.ensureStyles = function () {
        if (document.getElementById(api.STYLE_ID)) return;
        var style = document.createElement('style');
        style.id = api.STYLE_ID;
        style.textContent = [
            '.richtext-admin-wrapper{border:1px solid var(--border-color,#d0d7de);border-radius:6px;background:var(--body-bg,#fff);color:var(--body-fg,#1f2937);width:100%;max-width:920px;box-sizing:border-box;}',
            '.richtext-admin-toolbar{display:flex;flex-wrap:wrap;gap:4px;padding:6px;border-bottom:1px solid var(--hairline-color,#e5e7eb);background:var(--darkened-bg,#f8fafc);}',
            '.richtext-admin-toolbar button{border:1px solid var(--border-color,#d1d5db);background:var(--body-bg,#fff);color:var(--body-fg,#1f2937);border-radius:4px;padding:3px 8px;cursor:pointer;font-size:12px;}',
            '.richtext-admin-toolbar button:hover{background:var(--button-hover-bg,#f3f4f6);}',
            '.richtext-admin-toolbar button.is-active{background:var(--selected-bg,#dbeafe);border-color:var(--selected-row,#60a5fa);color:var(--selected-fg,#1e3a8a);}',
            '.richtext-admin-editor{min-height:180px;max-height:460px;overflow:auto;padding:10px;line-height:1.5;width:100%;box-sizing:border-box;outline:none;background:var(--body-bg,#fff);color:var(--body-fg,#1f2937);}',
            '.richtext-admin-editor:focus{outline:2px solid var(--primary,#79aec8);outline-offset:-2px;}',
            '.richtext-admin-editor p{margin:0.4em 0;}',
            '.richtext-admin-editor ul{display:block!important;list-style:none!important;margin:0.5em 0!important;padding-left:0!important;}',
            '.richtext-admin-editor ol{display:block!important;list-style:none!important;margin:0.5em 0!important;padding-left:0!important;counter-reset:richtext-list-item!important;}',
            '.richtext-admin-editor li{display:block!important;position:relative!important;margin:0.2em 0!important;padding-left:1.5em!important;}',
            '.richtext-admin-editor ul>li::before{content:"•";position:absolute;left:0.2em;}',
            '.richtext-admin-editor ol>li{counter-increment:richtext-list-item!important;}',
            '.richtext-admin-editor ol>li::before{content:counter(richtext-list-item)".";position:absolute;left:0;}',
            '.inline-group .richtext-admin-editor h1,.richtext-admin-wrapper .richtext-admin-editor h1{display:block!important;font-size:2em!important;font-weight:bold!important;margin:0.5em 0!important;padding:0!important;background:none!important;background-color:transparent!important;color:var(--body-fg)!important;border:none!important;box-shadow:none!important;text-transform:none!important;letter-spacing:normal!important;line-height:1.2!important;}',
            '.inline-group .richtext-admin-editor h2,.richtext-admin-wrapper .richtext-admin-editor h2{display:block!important;font-size:1.5em!important;font-weight:bold!important;margin:0.67em 0!important;padding:0!important;background:none!important;background-color:transparent!important;color:var(--body-fg)!important;border:none!important;box-shadow:none!important;text-transform:none!important;letter-spacing:normal!important;line-height:1.2!important;}',
            '.inline-group .richtext-admin-editor h3,.richtext-admin-wrapper .richtext-admin-editor h3{display:block!important;font-size:1.17em!important;font-weight:bold!important;margin:1em 0!important;padding:0!important;background:none!important;background-color:transparent!important;color:var(--body-fg)!important;border:none!important;box-shadow:none!important;text-transform:none!important;letter-spacing:normal!important;line-height:1.2!important;}',
            '.inline-group .richtext-admin-editor h4,.richtext-admin-wrapper .richtext-admin-editor h4{display:block!important;font-size:1em!important;font-weight:bold!important;margin:1.33em 0!important;padding:0!important;background:none!important;background-color:transparent!important;color:var(--body-fg)!important;border:none!important;box-shadow:none!important;text-transform:none!important;letter-spacing:normal!important;line-height:1.2!important;}',
        ].join('');
        document.body.appendChild(style);
    };

    // HTML helpers
    api.escapeHtml = function (v) {
        return String(v || '')
            .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    };

    api.looksLikeHtml        = function (v) { return /<\/?[a-z][\s\S]*>/i.test(v || ''); };
    api.looksLikeEscapedHtml = function (v) { return /&lt;\/?[a-z][\s\S]*&gt;/i.test(v || ''); };

    api.decodeHtmlEntities = function (v) {
        var d = document.createElement('textarea');
        d.innerHTML = v || '';
        return d.value;
    };

    var ALLOWED_TAGS = ['A','B','BR','EM','H1','H2','H3','H4','H5','H6','I','LI','OL','P','STRONG','U','UL','DIV'];

    api.getInlineTagAliases = function (tagName) {
        var tag = String(tagName || '').toUpperCase();
        if (tag === 'B' || tag === 'STRONG') return ['B', 'STRONG'];
        if (tag === 'I' || tag === 'EM') return ['I', 'EM'];
        if (tag === 'U') return ['U'];
        return [tag];
    };

    function serializeNode(node) {
        if (node.nodeType === Node.TEXT_NODE)    return api.escapeHtml(node.nodeValue);
        if (node.nodeType !== Node.ELEMENT_NODE) return '';
        var tag = node.tagName;
        if (ALLOWED_TAGS.indexOf(tag) === -1)    return api.escapeHtml(node.outerHTML);
        if (tag === 'BR') return '<br>';
        var children = Array.prototype.map.call(node.childNodes, serializeNode).join('');
        var t = tag.toLowerCase();
        if (tag === 'A') return '<a href="' + api.escapeHtml(node.getAttribute('href') || '') + '">' + children + '</a>';
        return '<' + t + '>' + children + '</' + t + '>';
    }

    api.buildPreviewHtml = function (value) {
        var decoded = api.decodeHtmlEntities(value || '');
        if (!decoded) return '';
        var c = document.createElement('div');
        c.innerHTML = decoded;
        return Array.prototype.map.call(c.childNodes, serializeNode).join('');
    };

    // Selection / range helpers
    api.getSelectionRange = function (editor) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return null;
        if (!editor.contains(sel.anchorNode) || !editor.contains(sel.focusNode)) return null;
        return sel.getRangeAt(0);
    };

    api.findAncestor = function (node, matcher, stopNode) {
        var cur = (node && node.nodeType === Node.TEXT_NODE) ? node.parentElement : node;
        while (cur && cur !== stopNode) {
            if (matcher(cur)) return cur;
            cur = cur.parentElement;
        }
        return null;
    };

    api.isBlockTag = function (tagName) {
        return /^H[1-6]$/.test(tagName) || tagName === 'P' || tagName === 'LI';
    };

    api.getCurrentBlockElement = function (editor) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return null;
        return api.findAncestor(sel.anchorNode, function (el) {
            return el.tagName && api.isBlockTag(el.tagName);
        }, editor);
    };

    api.getCurrentListElement = function (editor) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return null;
        return api.findAncestor(sel.anchorNode, function (el) {
            return el.tagName === 'UL' || el.tagName === 'OL';
        }, editor);
    };

    /*
     * Collect every text node that overlaps `range`.
     * Uses Range boundary comparison which is reliable cross-browser.
     */
    function getTextNodesInRange(range) {
        var root = range.commonAncestorContainer;
        if (root.nodeType === Node.TEXT_NODE) return [root];

        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
        var nodes  = [];
        var node;
        while ((node = walker.nextNode())) {
            var nr = document.createRange();
            nr.selectNodeContents(node);
            // Overlap = range starts before node ends  AND  range ends after node starts
            var startsBeforeNodeEnds = range.compareBoundaryPoints(Range.START_TO_END, nr) > 0;
            var endsAfterNodeStarts  = range.compareBoundaryPoints(Range.END_TO_START, nr) < 0;
            if (startsBeforeNodeEnds && endsAfterNodeStarts) nodes.push(node);
        }
        return nodes;
    }

    /*
     * Collapsed caret: walk up from anchorNode, ignore empty wrappers.
     * Real selection:  every text node inside the range must be a descendant
     *                  of a `tagName` element. Zero text nodes -> ancestor walk.
     */
    api.isInlineTagActive = function (editor, tagName) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || sel.rangeCount === 0) return false;

        var range = sel.getRangeAt(0);
        var tagNames = api.getInlineTagAliases(tagName);

        /* collapsed caret */
        if (range.collapsed) {
            var anc = api.findAncestor(sel.anchorNode, function (el) {
                return tagNames.indexOf(el.tagName) !== -1;
            }, editor);
            if (!anc) return false;
            // Ignore empty wrappers left after backspacing
            return anc.textContent.replace(/\u200B/g, '').trim() !== '';
        }

        /* real selection */
        var textNodes = getTextNodesInRange(range);

        if (textNodes.length === 0) {
            // Fallback: check from anchorNode
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

    /*
     * isInlineTagPresent - looser match for toolbar state.
     * Returns true when any part of the selection is within the tag.
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

    /*
     * getCurrentInlineElement - kept for callers in actions.js that need a
     * DOM handle (e.g. for single-element unwrap).
     * Returns the nearest tagName ancestor of anchorNode, but ONLY when the
     * whole selection is already active according to isInlineTagActive.
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

    // Empty inline cleanup
    api.removeEmptyInlineElements = function (editor) {
        var tags = ['B','I','U','A','EM','STRONG'];
        tags.forEach(function (tag) {
            var els = Array.prototype.slice.call(editor.querySelectorAll(tag));
            els.forEach(function (el) {
                if (el.parentNode && el.textContent.replace(/\u200B/g, '').trim() === '') {
                    api.unwrapElement(el);
                }
            });
        });
    };

    // Caret helpers
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

    api.selectNodeContents = function (node) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel) return;
        var range = document.createRange();
        range.selectNodeContents(node);
        sel.removeAllRanges();
        sel.addRange(range);
    };

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

    api.setCaretAtOffset = function (element, offset) {
        var sel = window.getSelection ? window.getSelection() : null;
        if (!sel || !element) return;
        var range  = document.createRange();
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

    // DOM mutation helpers
    api.replaceElementTagName = function (element, tagName) {
        var replacement = document.createElement(tagName);
        Array.prototype.forEach.call(element.attributes, function (attr) {
            replacement.setAttribute(attr.name, attr.value);
        });
        replacement.innerHTML = element.innerHTML;
        element.parentNode.replaceChild(replacement, element);
        return replacement;
    };

    api.unwrapElement = function (element) {
        var parent = element.parentNode;
        if (!parent) return;
        while (element.firstChild) parent.insertBefore(element.firstChild, element);
        parent.removeChild(element);
    };

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