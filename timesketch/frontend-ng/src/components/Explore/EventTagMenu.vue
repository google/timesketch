<template>
  <v-card min-width="500px" class="mx-auto">
    <v-card-text>
      Quick tags
      <v-chip-group>
        <v-chip
          v-for="tag in quickTags"
          :key="tag.tag"
          :color="tag.color"
          :text-color="tag.textColor"
          class="text-center"
          small
          @click="addTags(tag.tag)"
          >{{ tag.tag }}</v-chip
        >
      </v-chip-group>
      <br />
      <v-autocomplete
        v-model="selectedTags"
        :items="tags"
        outlined
        chips
        small-chips
        label="Add tag"
        multiple
      ></v-autocomplete>
      <v-btn outlined text small>Create new</v-btn>
    </v-card-text>
    <v-divider></v-divider>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn text>Save</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
export default {
  props: ['event'],
  data() {
    return {
      listItems: [],
      selectedTags: [],
      quickTags: [
        { tag: 'good', color: 'green', textColor: 'white' },
        { tag: 'bad', color: 'red', textColor: 'white' },
        { tag: 'suspicious', color: 'orange', textColor: 'white' },
      ],
    }
  },
  computed: {
    tags() {
      return this.$store.state.tags.map((tag) => tag.tag)
    },
  },
  methods: {
    addTags: function (tagsToAdd) {
      if (!Array.isArray(tagsToAdd)) {
        tagsToAdd = [tagsToAdd]
      }

      //if (tags.length) {
      //  EventBus.$emit('eventAnnotated', { type: '__ts_label', event: this.event, searchNode: this.currentSearchNode })
      //}

      tagsToAdd.forEach((tag) => {
        if (this.event._source.tag.indexOf(tag) === -1) {
          this.event._source.tag.push(tag)
          /*
          ApiClient.saveEventAnnotation(this.sketch.id, 'tag', tag, [this.event], this.currentSearchNode)
            .then((response) => {
              this.$emit('addLabel', label)
            })
            .catch((e) => {
              Toast.open('Error adding label')
              this.event._source.label = this.event._source.label.filter((e) => e !== label)
            })
            */
        }
      })
      /*
      if (this.labelsToRemove.length) {
        this.labelsToRemove.forEach((label) => {
          ApiClient.saveEventAnnotation(this.sketch.id, 'label', label, [this.event], this.currentSearchNode, true)
            .then((response) => {})
            .catch((e) => {})
          this.event._source.label = this.event._source.label.filter((e) => e !== label)
        })
        this.labelsToRemove = []
      }
      */
    },
  },
}
</script>

<style scoped lang="scss"></style>
