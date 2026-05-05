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
    /**
     * Injects the widget CSS once per page.
     */
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
    /**
     * Escapes HTML so it can be safely rendered as text.
     *
     * @param {string} v Raw input.
     * @returns {string} Escaped text.
     */
    api.escapeHtml = function (v) {
        return String(v || '')
            .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    };

    /**
     * Quick heuristic to check whether a string contains HTML tags.
     *
     * @param {string} v Candidate string.
     * @returns {boolean} True when the string looks like HTML.
     */
    api.looksLikeHtml        = function (v) { return /<\/?[a-z][\s\S]*>/i.test(v || ''); };
    /**
     * Detects escaped HTML sequences like &lt;tag&gt;.
     *
     * @param {string} v Candidate string.
     * @returns {boolean} True when the string looks like escaped HTML.
     */
    api.looksLikeEscapedHtml = function (v) { return /&lt;\/?[a-z][\s\S]*&gt;/i.test(v || ''); };

    /**
     * Decodes HTML entities into literal characters.
     *
     * @param {string} v HTML-encoded string.
     * @returns {string} Decoded string.
     */
    api.decodeHtmlEntities = function (v) {
        var d = document.createElement('textarea');
        d.innerHTML = v || '';
        return d.value;
    };

    var ALLOWED_TAGS = ['A','B','BR','EM','H1','H2','H3','H4','H5','H6','I','LI','OL','P','STRONG','U','UL','DIV'];

    /**
     * Normalizes inline tag aliases (e.g. B/STRONG, I/EM).
     *
     * @param {string} tagName Tag name to normalize.
     * @returns {string[]} Tag aliases to treat as equivalent.
     */
    api.getInlineTagAliases = function (tagName) {
        var tag = String(tagName || '').toUpperCase();
        if (tag === 'B' || tag === 'STRONG') return ['B', 'STRONG'];
        if (tag === 'I' || tag === 'EM') return ['I', 'EM'];
        if (tag === 'U') return ['U'];
        return [tag];
    };

    /**
     * Serializes an HTML node while keeping the allowed tag list.
     *
     * @param {Node} node Node to serialize.
     * @returns {string} Sanitized HTML output.
     */
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

    /**
     * Sanitizes HTML for displaying in the editor preview.
     *
     * @param {string} value Raw HTML string.
     * @returns {string} Safe HTML string.
     */
    api.buildPreviewHtml = function (value) {
        var decoded = api.decodeHtmlEntities(value || '');
        if (!decoded) return '';
        var c = document.createElement('div');
        c.innerHTML = decoded;
        return Array.prototype.map.call(c.childNodes, serializeNode).join('');
    };

})(window);