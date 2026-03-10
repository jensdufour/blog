<?php
/**
 * Server-side rendering for the theme/timeline block.
 *
 * @var array $attributes Block attributes.
 */

$items = $attributes['items'] ?? [];
if ( empty( $items ) ) {
    return;
}
?>
<div class="timeline">
<?php foreach ( $items as $item ) :
    $current_class = ! empty( $item['current'] ) ? ' current' : '';
    $date     = esc_html( $item['date'] ?? '' );
    $title    = esc_html( $item['title'] ?? '' );
    $subtitle = esc_html( $item['subtitle'] ?? '' );
    $content  = wp_kses_post( $item['content'] ?? '' );
?>
    <div class="timeline-item<?php echo $current_class; ?>">
        <?php if ( $date ) : ?><div class="timeline-date"><?php echo $date; ?></div><?php endif; ?>
        <?php if ( $title ) : ?><div class="timeline-title"><?php echo $title; ?></div><?php endif; ?>
        <?php if ( $subtitle ) : ?><div class="timeline-subtitle"><?php echo $subtitle; ?></div><?php endif; ?>
        <?php if ( $content ) : ?><div class="timeline-content"><?php echo $content; ?></div><?php endif; ?>
    </div>
<?php endforeach; ?>
</div>
