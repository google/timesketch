<template>
  <v-card class="mx-auto">
    <!--
    <v-list subheader>
      <v-subheader>Tag as:</v-subheader>

      <v-list-item-group multiple v-model="listItems">
        <v-list-item v-for="tag in tags" :key="tag.tag">
          <template v-slot:default="{ active }">
            <v-list-item-action>
              <v-checkbox dense :input-value="active" :value="tag.tag" v-model="selectedTags"></v-checkbox>
            </v-list-item-action>

            <v-list-item-content>
              <v-list-item-title>{{ tag.tag }}</v-list-item-title>
            </v-list-item-content>
          </template>
        </v-list-item>
      </v-list-item-group>
    </v-list>
    -->
    <v-card-text>
      Quick tags:
      <v-chip-group>
        <v-chip
          v-for="tag in quickTags"
          :key="tag.tag"
          :color="tag.color"
          :text-color="tag.textColor"
          class="text-center"
          >{{ tag.tag }}</v-chip
        >
      </v-chip-group>
      <!--
      <v-checkbox
        v-for="tag in quickTags"
        :key="tag"
        v-model="selectedTags"
        :value="tag"
        :label="tag"
        dense
      ></v-checkbox>
      -->

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
      <v-btn text small>Create new</v-btn>
      <v-btn text small>Manage tags</v-btn>
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
      selectedTags: ['win_crash'],
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
}
</script>

<style scoped lang="scss"></style>
