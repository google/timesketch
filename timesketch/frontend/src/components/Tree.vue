<template>
  <ul class="tree" v-if="Object.keys(treeData).length > 0">
    <node-tree :node="treeData" :handle-click="handleClick" :selected-node="selectedNode"></node-tree>
  </ul>
</template>

<script>
import NodeTree from './NodeTree'
import ApiClient from '../utils/RestApiClient'
import EventBus from '../main'

// Based on https://stackoverflow.com/a/54470906
function findSearchNode (object, key, predicate) {
  if (object.hasOwnProperty(key) && predicate(key, object[key]) === true) return object
  for (let i = 0; i < Object.keys(object).length; i++) {
    let value = object[Object.keys(object)[i]]
    if (typeof value === 'object' && value != null) {
      let searchNode = findSearchNode(value, key, predicate)
      if (searchNode != null) return searchNode
    }
  }
  return null
}

export default {
  components: { NodeTree },
  data () {
    return {
      treeData: {},
      selectedNode: null,
      initialNode: null
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    }
  },
  methods: {
    handleClick (node) {
      this.$emit('node-click', node)
      this.selectedNode = node
    },
    createBranch (newNode) {
      if (Object.keys(this.treeData).length === 0) {
        this.fetchHistory()
      }

      if (this.selectedNode) {
        if (this.selectedNode.id === newNode.id) {
          return
        }
        this.selectedNode.children.push(newNode)
        this.selectedNode = newNode
        return
      }

      let parent = findSearchNode(this.treeData, 'id', (k, v) => v === newNode.parent)
      if (parent) {
        if (parent.children.some(node => node.id === newNode.id)) {
          return
        }
        parent.children.push(newNode)
        this.selectedNode = newNode
        return
      }

      let node = findSearchNode(this.treeData, 'id', (k, v) => v === newNode.id)
      if (node) {
        this.selectedNode = node
      }
    },
    scrollTo () {
      document.getElementById(this.selectedNode.id.toString()).scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      })
    },
    fetchHistory () {
      ApiClient.getSearchHistory(this.sketch.id).then((response) => {
        this.treeData = response.data.objects[0]
        if (!this.selectedNode) {
          let lastNodeId = response.data.meta['last_node_id']
          this.selectedNode = findSearchNode(this.treeData, 'id', (k, v) => v === lastNodeId)
        }
      }).catch((e) => {})
    }
  },
  beforeDestroy () {
    EventBus.$off('createBranch')
  },
  created: function () {
    EventBus.$on('createBranch', this.createBranch)
    this.fetchHistory()
  },
  watch: {
    selectedNode: function () {
      this.$store.dispatch('updateSearchNode', this.selectedNode)
      this.$nextTick(function () {
        this.scrollTo()
      })
    }
  }

}
</script>

<style scoped lang="scss">

</style>
