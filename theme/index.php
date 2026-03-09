<?php get_header(); ?>

<?php if (have_posts()) : ?>
  <ul class="post-list">
    <?php while (have_posts()) : the_post(); ?>
      <li>
        <p class="post-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></p>
        <p class="post-meta">
          <?php echo get_the_date('F j, Y'); ?>
          <?php
          $categories = get_the_category();
          if ($categories) {
              $names = array_map(function($c) { return esc_html($c->name); }, $categories);
              echo ' &middot; ' . implode(', ', $names);
          }
          ?>
        </p>
      </li>
    <?php endwhile; ?>
  </ul>

  <?php
  $total = $GLOBALS['wp_query']->max_num_pages;
  if ($total > 1) : ?>
    <nav class="pagination">
      <?php
      echo paginate_links([
          'prev_text' => '&larr; Prev',
          'next_text' => 'Next &rarr;',
          'current'   => max(1, get_query_var('paged')),
          'total'     => $total,
      ]);
      ?>
    </nav>
  <?php endif; ?>

<?php else : ?>
  <p>No posts yet.</p>
<?php endif; ?>

<?php get_footer(); ?>
