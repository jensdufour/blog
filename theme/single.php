<?php get_header(); ?>

<?php while (have_posts()) : the_post(); ?>
  <article>
    <h1><?php the_title(); ?></h1>
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

    <?php if (has_post_thumbnail()) : ?>
      <?php the_post_thumbnail('full'); ?>
    <?php endif; ?>

    <div class="entry-content">
      <?php the_content(); ?>
    </div>
  </article>

  <nav class="post-nav">
    <span><?php previous_post_link('%link', '&larr; %title'); ?></span>
    <span><?php next_post_link('%link', '%title &rarr;'); ?></span>
  </nav>
<?php endwhile; ?>

<?php get_footer(); ?>
