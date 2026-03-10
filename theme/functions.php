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
