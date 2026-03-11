<?php
/**
 * Theme setup for FSE block theme.
 */

function jdm_setup() {
    add_theme_support('wp-block-styles');
    add_theme_support('editor-styles');
    add_editor_style('style.css');
    add_theme_support('comments');
}
add_action('after_setup_theme', 'jdm_setup');

function jdm_enqueue_styles() {
    wp_enqueue_style('jdm-style', get_stylesheet_uri(), [], wp_get_theme()->get('Version'));
}
add_action('wp_enqueue_scripts', 'jdm_enqueue_styles');

function jdm_theme_toggle_script() {
    ?>
    <script>
    (function() {
        var stored = localStorage.getItem('theme');
        if (stored) {
            document.documentElement.setAttribute('data-theme', stored);
        }
    })();
    </script>
    <?php
}
add_action('wp_head', 'jdm_theme_toggle_script', 1);

function jdm_toggle_inline_script() {
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var btn = document.querySelector('.theme-toggle');
        if (!btn) return;
        function updateIcon() {
            var theme = document.documentElement.getAttribute('data-theme');
            if (!theme) {
                theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            }
            btn.textContent = theme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
        }
        updateIcon();
        btn.addEventListener('click', function() {
            var current = document.documentElement.getAttribute('data-theme');
            if (!current) {
                current = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            }
            var next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            updateIcon();
        });
    });
    </script>
    <?php
}
add_action('wp_footer', 'jdm_toggle_inline_script');

/* Remove unnecessary WordPress head clutter */
remove_action('wp_head', 'wp_generator');
remove_action('wp_head', 'wlwmanifest_link');
remove_action('wp_head', 'rsd_link');
remove_action('wp_head', 'wp_shortlink_wp_head');
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');

/* Register Yoast SEO meta fields for REST API access */
function jdm_register_yoast_meta() {
    $meta_keys = [
        '_yoast_wpseo_title',
        '_yoast_wpseo_metadesc',
        '_yoast_wpseo_focuskw',
    ];
    foreach ( ['post', 'page'] as $post_type ) {
        foreach ( $meta_keys as $key ) {
            register_post_meta( $post_type, $key, [
                'show_in_rest'  => true,
                'single'        => true,
                'type'          => 'string',
                'auth_callback' => function() { return current_user_can( 'edit_posts' ); },
            ] );
        }
    }
}
add_action( 'init', 'jdm_register_yoast_meta' );

/* Replace chain icon with Sessionize logo for sessionize.com social links */
function jdm_sessionize_social_icon( $block_content, $block ) {
    if ( $block['blockName'] !== 'core/social-link' ) {
        return $block_content;
    }
    if ( empty( $block['attrs']['url'] ) || strpos( $block['attrs']['url'], 'sessionize.com' ) === false ) {
        return $block_content;
    }
    $sessionize_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm1.2 17.4H6.6v-2.4h6.6v2.4zm4.2-4.2H6.6v-2.4h10.8v2.4zm0-4.2H6.6V6.6h10.8V9z" fill="currentColor"/></svg>';
    $block_content = preg_replace( '/<svg[^>]*>.*?<\/svg>/s', $sessionize_svg, $block_content, 1 );
    return $block_content;
}
add_filter( 'render_block', 'jdm_sessionize_social_icon', 10, 2 );

/* Register custom blocks bundled with the theme */
function jdm_register_blocks() {
    register_block_type( get_template_directory() . '/blocks/timeline' );
}
add_action( 'init', 'jdm_register_blocks' );
