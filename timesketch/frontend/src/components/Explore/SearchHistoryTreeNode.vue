<template>
  <li>
    <span
      @click="handleClick(node)"
      :class="[{ active: isSelected }, { star: hasStar && !isSelected }, { dimmed: count === 0 && !isSelected }]"
      :id="node.id"
      style="min-width:205px;"
    >
      <i
        v-if="hasStar"
        class="fas fa-star"
        style="float:left; color: #FFD700; -webkit-text-stroke-width: 1px; -webkit-text-stroke-color: #777777; margin-right:10px; margin-top:3px;"
      ></i>
      <i v-if="hasComment" class="fas fa-comment" style="float:left; margin-right:10px; margin-top:3px;"></i>
      <i v-if="hasLabel" class="fas fa-tag" style="float:left; margin-right:10px; margin-top:3px;"></i>
      <div class="query-string" :class="[{ 'query-string-active': isSelected }]" style="float:left;">
        {{ node.query_string }}
      </div>
      <div class="tag is-light" style="margin-left:10px; margin-right: -5px; float:right;">
        {{ count | compactNumber }}
      </div>
    </span>

    <ul v-if="node.children && node.children.length">
      <node
        v-for="child in node.children"
        :node="child"
        :key="child.id"
        :handle-click="handleClick"
        :selected-node="selectedNode"
      ></node>
    </ul>
  </li>
</template>

<script>
export default {
  name: 'node',
  props: {
    node: Object,
    handleClick: Function,
    selectedNode: Object,
  },
  computed: {
    hasStar() {
      return this.node.labels.includes('__ts_star')
    },
    hasLabel() {
      return this.node.labels.includes('__ts_label')
    },
    hasComment() {
      return this.node.labels.includes('__ts_comment')
    },
    isSelected() {
      return this.selectedNode.id === this.node.id
    },
    count() {
      return this.node.query_result_count || 0
    },
  },
}
</script>

<style scoped lang="scss">
.active {
  background-color: rgb(66, 133, 244);
  color: white;
}
.star {
  background-color: #feefc3;
  color: #333333;
}
.dimmed {
  opacity: 0.5;
}
.query-string {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
  word-wrap: break-word;
  color: var(--font-color-dark);
}
.query-string-active {
  color: var(--font-color-light);
}
</style>
