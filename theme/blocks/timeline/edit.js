( function() {
	var el = wp.element.createElement;
	var registerBlockType = wp.blocks.registerBlockType;
	var ServerSideRender = wp.serverSideRender;
	var useBlockProps = wp.blockEditor.useBlockProps;

	registerBlockType( 'theme/timeline', {
		edit: function( props ) {
			return el( 'div', useBlockProps(),
				el( ServerSideRender, {
					block: 'theme/timeline',
					attributes: props.attributes,
				} )
			);
		},
		save: function() {
			return null;
		},
	} );
} )();
