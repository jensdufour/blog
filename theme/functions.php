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
        requestAnimationFrame(function() {
            document.body.classList.add('transitions-ready');
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

/* ── Performance optimizations ── */

/* Set fetchpriority="high" on the featured image (LCP element) on single posts */
function jdm_featured_image_fetchpriority( $attr, $attachment, $size ) {
    if ( is_singular( 'post' ) && has_post_thumbnail() && get_post_thumbnail_id() === $attachment->ID ) {
        $attr['fetchpriority'] = 'high';
        $attr['loading'] = false;
        $attr['decoding'] = 'async';
    }
    return $attr;
}
add_filter( 'wp_get_attachment_image_attributes', 'jdm_featured_image_fetchpriority', 10, 3 );

/* Remove WordPress block library CSS on pages that don't need it */
function jdm_dequeue_block_styles() {
    /* Remove classic-theme-styles since this is a block theme with its own style.css + theme.json */
    wp_dequeue_style( 'classic-theme-styles' );

    /* Dequeue wp-block-library on the front page where most blocks are simple */
    if ( is_front_page() ) {
        wp_dequeue_style( 'wp-block-library' );
    }
}
add_action( 'wp_enqueue_scripts', 'jdm_dequeue_block_styles', 20 );

/* Disable Gravatar requests entirely (not used, saves external HTTP calls) */
add_filter( 'option_show_avatars', '__return_false' );

/* Remove Gravatar dns-prefetch since avatars are disabled */
function jdm_remove_gravatar_dns( $urls, $relation_type ) {
    if ( $relation_type === 'dns-prefetch' ) {
        $urls = array_filter( $urls, function( $url ) {
            return strpos( $url, 'gravatar.com' ) === false
                && strpos( $url, 'secure.gravatar.com' ) === false;
        } );
    }
    return $urls;
}
add_filter( 'wp_resource_hints', 'jdm_remove_gravatar_dns', 10, 2 );

/* Remove jQuery migrate on the front end (not needed for this theme) */
function jdm_remove_jquery_migrate( $scripts ) {
    if ( ! is_admin() && isset( $scripts->registered['jquery'] ) ) {
        $scripts->registered['jquery']->deps = array_diff(
            $scripts->registered['jquery']->deps,
            [ 'jquery-migrate' ]
        );
    }
}
add_action( 'wp_default_scripts', 'jdm_remove_jquery_migrate' );

/* Set cache-control headers for theme assets */
function jdm_cache_headers() {
    if ( is_admin() ) {
        return;
    }
    /* Only add cache headers for non-logged-in users viewing the front end */
    if ( ! is_user_logged_in() ) {
        header( 'Cache-Control: public, max-age=86400, s-maxage=604800' );
    }
}
add_action( 'send_headers', 'jdm_cache_headers' );

/* Disable self-pingbacks */
function jdm_disable_self_pingback( &$links ) {
    $home = home_url();
    foreach ( $links as $l => $link ) {
        if ( strpos( $link, $home ) === 0 ) {
            unset( $links[ $l ] );
        }
    }
}
add_action( 'pre_ping', 'jdm_disable_self_pingback' );

/* Add lazy loading to footer certificate badge images */
function jdm_lazy_load_cert_badges( $block_content, $block ) {
    if ( $block['blockName'] !== 'core/image' ) {
        return $block_content;
    }
    if ( empty( $block['attrs']['className'] ) || strpos( $block['attrs']['className'], 'cert-badge' ) === false ) {
        return $block_content;
    }
    $block_content = str_replace( '<img ', '<img loading="lazy" decoding="async" ', $block_content );
    return $block_content;
}
add_filter( 'render_block', 'jdm_lazy_load_cert_badges', 10, 2 );

/* Fix Yoast robots.txt Schemamap line break that causes a parsing error */
function jdm_fix_robots_txt( $output ) {
    /* Collapse "Schemamap:\n<url>" onto a single line */
    $output = preg_replace( '/Schemamap:\s*\n\s*/i', 'Schemamap: ', $output );
    return $output;
}
add_filter( 'robots_txt', 'jdm_fix_robots_txt', 999 );
