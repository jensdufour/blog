(function () {
	var el = wp.element.createElement;
	var registerBlockType = wp.blocks.registerBlockType;
	var useBlockProps = wp.blockEditor.useBlockProps;
	var InspectorControls = wp.blockEditor.InspectorControls;
	var RichText = wp.blockEditor.RichText;
	var Fragment = wp.element.Fragment;
	var Button = wp.components.Button;
	var PanelBody = wp.components.PanelBody;
	var TextControl = wp.components.TextControl;
	var ToggleControl = wp.components.ToggleControl;

	function emptyItem() {
		return { date: '', title: '', subtitle: '', content: '', current: false };
	}

	function updateItem(items, index, key, value, setAttributes) {
		var updated = items.map(function (item, i) {
			if (i !== index) return item;
			var copy = {};
			for (var k in item) copy[k] = item[k];
			copy[key] = value;
			return copy;
		});
		setAttributes({ items: updated });
	}

	function removeItem(items, index, setAttributes) {
		setAttributes({ items: items.filter(function (_, i) { return i !== index; }) });
	}

	function moveItem(items, index, direction, setAttributes) {
		var target = index + direction;
		if (target < 0 || target >= items.length) return;
		var updated = items.slice();
		var temp = updated[index];
		updated[index] = updated[target];
		updated[target] = temp;
		setAttributes({ items: updated });
	}

	registerBlockType('theme/timeline', {
		edit: function (props) {
			var items = props.attributes.items || [];
			var setAttributes = props.setAttributes;
			var blockProps = useBlockProps();

			return el(Fragment, null,

				/* ── Sidebar: manage items ── */
				el(InspectorControls, null,
					el(PanelBody, { title: 'Timeline Items', initialOpen: true },
						items.map(function (item, i) {
							return el(PanelBody, { key: i, title: item.title || '(Item ' + (i + 1) + ')', initialOpen: false },
								el(TextControl, {
									label: 'Date',
									value: item.date || '',
									onChange: function (v) { updateItem(items, i, 'date', v, setAttributes); },
								}),
								el(TextControl, {
									label: 'Title',
									value: item.title || '',
									onChange: function (v) { updateItem(items, i, 'title', v, setAttributes); },
								}),
								el(TextControl, {
									label: 'Subtitle',
									value: item.subtitle || '',
									onChange: function (v) { updateItem(items, i, 'subtitle', v, setAttributes); },
								}),
								el(TextControl, {
									label: 'Content (HTML allowed)',
									value: item.content || '',
									onChange: function (v) { updateItem(items, i, 'content', v, setAttributes); },
								}),
								el(ToggleControl, {
									label: 'Current',
									checked: !!item.current,
									onChange: function (v) { updateItem(items, i, 'current', v, setAttributes); },
								}),
								el('div', { style: { display: 'flex', gap: '4px', marginTop: '8px' } },
									el(Button, {
										icon: 'arrow-up-alt',
										label: 'Move up',
										size: 'small',
										disabled: i === 0,
										onClick: function () { moveItem(items, i, -1, setAttributes); },
									}),
									el(Button, {
										icon: 'arrow-down-alt',
										label: 'Move down',
										size: 'small',
										disabled: i === items.length - 1,
										onClick: function () { moveItem(items, i, 1, setAttributes); },
									}),
									el(Button, {
										icon: 'trash',
										label: 'Remove item',
										size: 'small',
										isDestructive: true,
										onClick: function () { removeItem(items, i, setAttributes); },
									})
								)
							);
						}),
						el(Button, {
							variant: 'secondary',
							onClick: function () { setAttributes({ items: items.concat([emptyItem()]) }); },
							style: { marginTop: '12px' },
						}, '+ Add Item')
					)
				),

				/* ── Editor preview: inline editable timeline ── */
				el('div', blockProps,
					items.length === 0
						? el('p', { style: { color: '#999', fontStyle: 'italic' } }, 'No timeline items yet. Use the sidebar or click "+ Add Item" below to get started.')
						: el('div', { className: 'timeline' },
							items.map(function (item, i) {
								return el('div', { key: i, className: 'timeline-item' + (item.current ? ' current' : '') },
									el(RichText, {
										tagName: 'div',
										className: 'timeline-date',
										value: item.date || '',
										onChange: function (v) { updateItem(items, i, 'date', v, setAttributes); },
										placeholder: 'Date...',
									}),
									el(RichText, {
										tagName: 'div',
										className: 'timeline-title',
										value: item.title || '',
										onChange: function (v) { updateItem(items, i, 'title', v, setAttributes); },
										placeholder: 'Title...',
									}),
									el(RichText, {
										tagName: 'div',
										className: 'timeline-subtitle',
										value: item.subtitle || '',
										onChange: function (v) { updateItem(items, i, 'subtitle', v, setAttributes); },
										placeholder: 'Subtitle...',
									}),
									el(RichText, {
										tagName: 'div',
										className: 'timeline-content',
										value: item.content || '',
										onChange: function (v) { updateItem(items, i, 'content', v, setAttributes); },
										placeholder: 'Content...',
										multiline: 'p',
									})
								);
							})
						),
					el('div', { style: { textAlign: 'center', marginTop: '16px' } },
						el(Button, {
							variant: 'secondary',
							onClick: function () { setAttributes({ items: items.concat([emptyItem()]) }); },
						}, '+ Add Item')
					)
				)
			);
		},

		save: function () {
			return null;
		},
	});
})();
