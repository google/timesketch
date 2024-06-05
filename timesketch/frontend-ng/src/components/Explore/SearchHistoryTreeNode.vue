<template>
  <li>
    <span
      @click="handleClick(node)"
      :class="[{ active: isSelected }, { star: hasStar && !isSelected }, { dimmed: count === 0 && !isSelected }]"
      :id="node.id"
      style="min-width: 280px"
    >
      <v-icon title="Added a Star to an event" v-if="hasStar" style="float: left" class="mr-1" color="amber darken-2"
        >mdi-star</v-icon
      >
      <v-icon title="Added a Comment to an event" v-if="hasComment" style="float: left" class="mr-1"
        >mdi-comment-outline</v-icon
      >
      <v-icon title="Added a Label to an event" v-if="hasLabel" style="float: left; margin-right: 10px"
        >mdi-label</v-icon
      >
      <v-tooltip bottom>
        <template v-slot:activator="{ on, attrs }">
          <div
            v-bind="attrs"
            v-on="on"
            class="query-string"
            :class="[{ 'query-string-active': isSelected }]"
            style="float: left"
          >
            {{ node.query_string }}
          </div>
        </template>
        <span>{{ node.query_string }} {{ node }}</span>
      </v-tooltip>

      <div class="tag is-light" style="margin-left: 5px; float: right">
        <small>{{ count | compactNumber }}</small>
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
  background-color: #fee9a8;
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
