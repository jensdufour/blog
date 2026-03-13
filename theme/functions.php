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

/* Theme stylesheet is inlined via jdm_inline_theme_styles — no external CSS enqueue needed */

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

/* Remove unused stylesheets and inline the navigation block CSS */
function jdm_dequeue_block_styles() {
    wp_dequeue_style( 'classic-theme-styles' );
    /* Dequeue navigation CSS so W3TC doesn't bundle it into a render-blocking file.
       It will be inlined by jdm_inline_nav_styles instead. */
    wp_dequeue_style( 'wp-block-navigation' );
}
add_action( 'wp_enqueue_scripts', 'jdm_dequeue_block_styles', 20 );

/* Inline the navigation block CSS to avoid a render-blocking request */
function jdm_inline_nav_styles() {
    $nav_css = ABSPATH . WPINC . '/blocks/navigation/style.min.css';
    if ( file_exists( $nav_css ) ) {
        echo '<style id="wp-block-navigation-inline">' . file_get_contents( $nav_css ) . '</style>' . "\n";
    }
}
add_action( 'wp_head', 'jdm_inline_nav_styles', 9 );

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

/* Inline the small theme stylesheet to eliminate render-blocking CSS request */
function jdm_inline_theme_styles() {
    $css_file = get_template_directory() . '/style.css';
    if ( file_exists( $css_file ) ) {
        $css = file_get_contents( $css_file );
        /* Strip the file header comment block */
        $css = preg_replace( '/\/\*[\s\S]*?\*\/\s*/', '', $css, 1 );
        echo '<style id="jdm-inline-style">' . $css . '</style>' . "\n";
    }
}
add_action( 'wp_head', 'jdm_inline_theme_styles', 8 );

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

/* Delay Google Tag Manager to keep it off the critical rendering path.
   Replaces GTM's script tag with a lightweight loader that fetches it
   after the page becomes interactive (3s delay or requestIdleCallback). */
function jdm_delay_gtm() {
    if ( is_admin() ) {
        return;
    }
    /* Remove Site Kit's default GTM output and replace with delayed version */
    ob_start( function( $html ) {
        /* Find and remove the gtag.js script tag */
        $pattern = '/<script[^>]*src=["\'][^"\']*googletagmanager\.com\/gtag\/js[^"\']*["\'][^>]*><\/script>/i';
        if ( preg_match( $pattern, $html, $matches ) ) {
            $html = str_replace( $matches[0], '', $html );
            /* Inject a delayed loader before </body> */
            $loader = '<script>setTimeout(function(){var s=document.createElement("script");s.src="' .
                esc_url( 'https://www.googletagmanager.com/gtag/js?id=GT-TNF9L36X' ) .
                '";s.async=true;document.head.appendChild(s)},3000);</script>';
            $html = str_replace( '</body>', $loader . '</body>', $html );
        }
        return $html;
    } );
}
add_action( 'template_redirect', 'jdm_delay_gtm', 0 );

/* Add cache headers for static theme assets served via PHP */
function jdm_send_cache_headers() {
    if ( is_admin() || is_user_logged_in() ) {
        return;
    }
    /* Set cache headers on the HTML response */
    header( 'Cache-Control: public, max-age=3600, s-maxage=86400' );
}
add_action( 'send_headers', 'jdm_send_cache_headers' );

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

/* Fix Yoast robots.txt: remove non-standard Schemamap directive (flagged as
   "Unknown directive" by PageSpeed) and fix line break formatting */
function jdm_fix_robots_txt( $output ) {
    /* Remove the entire Schemamap line (non-standard, causes SEO flag) */
    $output = preg_replace( '/^Schemamap:.*$/mi', '', $output );
    /* Also fix "User-agent:\n*" if split across lines */
    $output = preg_replace( '/User-agent:\s*\n\s*\*/i', 'User-agent: *', $output );
    /* Clean up any resulting blank lines */
    $output = preg_replace( '/\n{3,}/', "\n\n", $output );
    return $output;
}
add_filter( 'robots_txt', 'jdm_fix_robots_txt', 999, 2 );

/* Register a shortcode that renders a "Report an issue" link for the current post */
function jdm_report_issue_shortcode() {
    if ( ! is_singular( 'post' ) ) {
        return '';
    }
    $title = rawurlencode( 'Issue with: ' . get_the_title() );
    $url   = get_permalink();
    $body  = rawurlencode( "**Page:** {$url}\n\n**Describe the issue:**\n" );
    $href  = "https://github.com/jensdufour/blog/issues/new?title={$title}&body={$body}&labels=content";
    return '<div class="report-issue"><a href="' . esc_url( $href ) . '" target="_blank" rel="noopener noreferrer">Spotted something wrong? Report an issue on GitHub</a></div>';
}
add_shortcode( 'report_issue', 'jdm_report_issue_shortcode' );
