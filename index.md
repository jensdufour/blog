---
layout: default
title: Home
---

<ul class="post-list">
  {% assign sorted_posts = site.posts | sort: "date" | reverse %}
  {% for post in sorted_posts %}
    {% if post.status == "publish" or post.status == nil %}
    <li>
      <h2><a href="{{ post.url | prepend: site.baseurl }}">{{ post.title }}</a></h2>
      <p class="post-meta">
        {{ post.date | date: "%B %-d, %Y" }}
        {% if post.categories.size > 0 %}
          &middot;
          {% for cat in post.categories %}{{ cat }}{% unless forloop.last %}, {% endunless %}{% endfor %}
        {% endif %}
      </p>
      <p>{{ post.content | strip_html | truncatewords: 50 }}</p>
    </li>
    {% endif %}
  {% endfor %}
</ul>
