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
   "Unknown directive" by PageSpeed) and fix line break formatting.
   Use PHP_INT_MAX priority so we run AFTER Yoast adds its directives. */
function jdm_fix_robots_txt( $output ) {
    /* Remove the Schemamap line (handles both single-line and split formats) */
    $output = preg_replace( '/^Schemamap:.*$/mi', '', $output );
    /* Fix "User-agent:\n*" split across lines */
    $output = preg_replace( '/User-agent:\s*\n\s*\*/i', 'User-agent: *', $output );
    /* Clean up any resulting blank lines */
    $output = preg_replace( '/\n{3,}/', "\n\n", $output );
    return $output;
}
add_filter( 'robots_txt', 'jdm_fix_robots_txt', PHP_INT_MAX, 2 );

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

/* ── Reading time estimate ── */
function jdm_reading_time_after_date( $block_content, $block ) {
    if ( $block['blockName'] !== 'core/post-date' ) {
        return $block_content;
    }
    $post = get_post();
    if ( ! $post || $post->post_type !== 'post' ) {
        return $block_content;
    }
    $word_count = str_word_count( wp_strip_all_tags( $post->post_content ) );
    $minutes = max( 1, (int) ceil( $word_count / 200 ) );
    $reading_time = '<span class="reading-time">&middot; ' . $minutes . ' min read</span>';
    /* Insert before the closing tag of the date wrapper */
    $block_content = preg_replace( '/<\/div>$/i', $reading_time . '</div>', $block_content, 1 );
    return $block_content;
}
add_filter( 'render_block', 'jdm_reading_time_after_date', 10, 2 );

/* ── Clickable post cards on home page ── */
function jdm_clickable_post_cards_script() {
    if ( ! is_home() && ! is_front_page() ) {
        return;
    }
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.wp-block-post-template .wp-block-group').forEach(function(card) {
            var link = card.querySelector('.wp-block-post-title a');
            if (!link) return;
            card.style.cursor = 'pointer';
            card.addEventListener('click', function(e) {
                if (e.target.closest('a')) return;
                link.click();
            });
        });
    });
    </script>
    <?php
}
add_action( 'wp_footer', 'jdm_clickable_post_cards_script' );

/* ── Sticky Table of Contents (single posts only) ── */
function jdm_toc_script() {
    if ( ! is_singular( 'post' ) ) {
        return;
    }
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var content = document.querySelector('.entry-content, .wp-block-post-content');
        if (!content) return;
        var headings = content.querySelectorAll('h2, h3');
        if (headings.length < 2) return;

        var nav = document.createElement('nav');
        nav.className = 'toc-sidebar';
        nav.setAttribute('aria-label', 'Table of contents');
        var title = document.createElement('span');
        title.className = 'toc-title';
        title.textContent = 'On this page';
        nav.appendChild(title);
        var ul = document.createElement('ul');

        headings.forEach(function(h, i) {
            if (!h.id) h.id = 'heading-' + i;
            var li = document.createElement('li');
            li.className = h.tagName === 'H3' ? 'toc-h3' : '';
            var a = document.createElement('a');
            a.href = '#' + h.id;
            a.textContent = h.textContent;
            li.appendChild(a);
            ul.appendChild(li);
        });
        nav.appendChild(ul);
        document.body.appendChild(nav);

        var links = ul.querySelectorAll('a');
        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    links.forEach(function(l) { l.classList.remove('active'); });
                    var active = ul.querySelector('a[href="#' + entry.target.id + '"]');
                    if (active) active.classList.add('active');
                }
            });
        }, { rootMargin: '0px 0px -70% 0px', threshold: 0 });

        headings.forEach(function(h) { observer.observe(h); });
    });
    </script>
    <?php
}
add_action( 'wp_footer', 'jdm_toc_script' );

/* ── Sessionize timeline: wrap each title + its items into a .sz-session div ── */
function jdm_sessionize_session_wrapper_script() {
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.sz-group').forEach(function(group) {
            var children = Array.from(group.children);
            children.forEach(function(el) {
                if (el.classList.contains('sz-item')) {
                    var session = document.createElement('div');
                    session.className = 'sz-session';
                    el.before(session);
                    session.appendChild(el);
                }
            });
        });

        /* Make timeline cards and Sessionize sessions fully clickable */
        document.querySelectorAll('.sz-session, .timeline-item').forEach(function(card) {
            var link = card.querySelector('a');
            if (!link) return;
            card.style.cursor = 'pointer';
            card.addEventListener('click', function(e) {
                if (e.target.closest('a')) return;
                link.click();
            });
        });
    });
    </script>
    <?php
}
add_action( 'wp_footer', 'jdm_sessionize_session_wrapper_script' );

/* ── Search index REST endpoint ── */
function jdm_register_search_index_endpoint() {
    register_rest_route( 'jdm/v1', '/search-index', [
        'methods'             => 'GET',
        'callback'            => 'jdm_search_index_callback',
        'permission_callback' => '__return_true',
    ] );
}
add_action( 'rest_api_init', 'jdm_register_search_index_endpoint' );

function jdm_search_index_callback() {
    $posts = get_posts( [
        'post_type'      => 'post',
        'post_status'    => 'publish',
        'posts_per_page' => -1,
        'orderby'        => 'date',
        'order'          => 'DESC',
    ] );

    $index = [];
    foreach ( $posts as $p ) {
        $tags = wp_get_post_tags( $p->ID, [ 'fields' => 'names' ] );
        $index[] = [
            'title'   => html_entity_decode( get_the_title( $p ), ENT_QUOTES, 'UTF-8' ),
            'excerpt' => wp_trim_words( wp_strip_all_tags( $p->post_content ), 30, '...' ),
            'tags'    => $tags,
            'link'    => get_permalink( $p ),
            'date'    => get_the_date( 'c', $p ),
        ];
    }

    return new WP_REST_Response( $index, 200, [
        'Cache-Control' => 'public, max-age=3600',
    ] );
}

/* ── Search modal ── */
function jdm_search_modal() {
    ?>
    <div class="search-overlay" id="searchOverlay">
        <div class="search-modal" role="dialog" aria-label="Search posts">
            <div class="search-modal-input-wrap">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input class="search-modal-input" id="searchInput" type="text" placeholder="Search posts..." autocomplete="off" />
                <kbd class="search-modal-kbd">ESC</kbd>
            </div>
            <div class="search-results" id="searchResults"></div>
        </div>
    </div>
    <script>
    (function() {
        var overlay = document.getElementById('searchOverlay');
        var input = document.getElementById('searchInput');
        var results = document.getElementById('searchResults');
        var activeIdx = -1;
        var indexCache = null;
        var indexUrl = '<?php echo esc_url( rest_url( 'jdm/v1/search-index' ) ); ?>';

        function loadIndex() {
            if (indexCache) return Promise.resolve(indexCache);
            var cached = sessionStorage.getItem('jdm_search_index');
            var cachedAt = sessionStorage.getItem('jdm_search_index_ts');
            if (cached && cachedAt && (Date.now() - parseInt(cachedAt, 10)) < 3600000) {
                indexCache = JSON.parse(cached);
                return Promise.resolve(indexCache);
            }
            return fetch(indexUrl)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    indexCache = data;
                    sessionStorage.setItem('jdm_search_index', JSON.stringify(data));
                    sessionStorage.setItem('jdm_search_index_ts', String(Date.now()));
                    return data;
                });
        }

        function openSearch() {
            overlay.classList.add('open');
            input.value = '';
            results.innerHTML = '';
            activeIdx = -1;
            loadIndex();
            setTimeout(function() { input.focus(); }, 50);
        }

        function closeSearch() {
            overlay.classList.remove('open');
            input.value = '';
            results.innerHTML = '';
            activeIdx = -1;
        }

        /* Toggle button */
        var btn = document.querySelector('.search-toggle');
        if (btn) btn.addEventListener('click', openSearch);

        /* Ctrl/Cmd + K shortcut */
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                if (overlay.classList.contains('open')) closeSearch();
                else openSearch();
            }
            if (e.key === 'Escape' && overlay.classList.contains('open')) {
                closeSearch();
            }
        });

        /* Click outside to close */
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) closeSearch();
        });

        /* Format date */
        function fmtDate(dateStr) {
            var d = new Date(dateStr);
            return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        }

        /* Score a post against the query (higher = better match) */
        function score(post, terms) {
            var s = 0;
            var titleLower = post.title.toLowerCase();
            var excerptLower = post.excerpt.toLowerCase();
            var tagsLower = post.tags.map(function(t) { return t.toLowerCase(); });

            for (var i = 0; i < terms.length; i++) {
                var t = terms[i];
                /* Exact title match */
                if (titleLower === t) { s += 100; continue; }
                /* Title starts with term */
                if (titleLower.indexOf(t) === 0) { s += 60; continue; }
                /* Title contains term */
                if (titleLower.indexOf(t) !== -1) { s += 40; continue; }
                /* Tag exact match */
                var tagMatch = false;
                for (var j = 0; j < tagsLower.length; j++) {
                    if (tagsLower[j] === t) { s += 35; tagMatch = true; break; }
                    if (tagsLower[j].indexOf(t) !== -1) { s += 20; tagMatch = true; break; }
                }
                if (tagMatch) continue;
                /* Excerpt contains term */
                if (excerptLower.indexOf(t) !== -1) { s += 10; continue; }
                /* No match for this term: penalize */
                s -= 20;
            }
            return s;
        }

        /* Search the index and return ranked results */
        function search(query) {
            if (!indexCache) return [];
            var terms = query.toLowerCase().split(/\s+/).filter(function(t) { return t.length > 0; });
            if (!terms.length) return [];
            var scored = indexCache.map(function(p) {
                return { post: p, score: score(p, terms) };
            }).filter(function(r) { return r.score > 0; });
            scored.sort(function(a, b) { return b.score - a.score; });
            return scored.slice(0, 8).map(function(r) { return r.post; });
        }

        /* Render results */
        function render(posts, query) {
            if (!query) { results.innerHTML = ''; activeIdx = -1; return; }
            if (posts.length === 0) {
                results.innerHTML = '<div class="search-no-results">No posts found</div>';
                activeIdx = -1;
                return;
            }
            results.innerHTML = posts.map(function(p) {
                var tags = p.tags.length ? '<span class="search-result-tags">' + p.tags.join(', ') + '</span>' : '';
                return '<a class="search-result-item" href="' + p.link + '">' +
                    '<div class="search-result-title">' + p.title + '</div>' +
                    '<div class="search-result-excerpt">' + p.excerpt + '</div>' +
                    '<div class="search-result-meta">' + fmtDate(p.date) + (tags ? ' &middot; ' + tags : '') + '</div>' +
                    '</a>';
            }).join('');
            activeIdx = -1;
        }

        /* Highlight active item */
        function updateActive() {
            var items = results.querySelectorAll('.search-result-item');
            items.forEach(function(el, i) {
                el.classList.toggle('active', i === activeIdx);
                if (i === activeIdx) el.scrollIntoView({ block: 'nearest' });
            });
        }

        /* Keyboard navigation inside results */
        input.addEventListener('keydown', function(e) {
            var items = results.querySelectorAll('.search-result-item');
            if (!items.length) return;
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIdx = (activeIdx + 1) % items.length;
                updateActive();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIdx = (activeIdx - 1 + items.length) % items.length;
                updateActive();
            } else if (e.key === 'Enter' && activeIdx >= 0) {
                e.preventDefault();
                items[activeIdx].click();
            }
        });

        /* Instant client-side search on every keystroke */
        input.addEventListener('input', function() {
            var q = input.value.trim();
            if (q.length < 2) { results.innerHTML = ''; activeIdx = -1; return; }
            loadIndex().then(function() {
                render(search(q), q);
            });
        });
    })();
    </script>
    <?php
}
add_action( 'wp_footer', 'jdm_search_modal' );

/* ── Back to Top button ── */
function jdm_back_to_top_script() {
    ?>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var btn = document.createElement('button');
        btn.className = 'back-to-top';
        btn.setAttribute('aria-label', 'Back to top');
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"></polyline></svg>';
        document.body.appendChild(btn);
        window.addEventListener('scroll', function() {
            btn.classList.toggle('visible', window.scrollY > 400);
        }, { passive: true });
        btn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });
    </script>
    <?php
}
add_action( 'wp_footer', 'jdm_back_to_top_script' );
