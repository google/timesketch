<template>
  <div>
    <section class="box">
      <h1 class="subtitle">Compose IOC</h1>
      <b-field label-position="on-border">
        <b-input custom-class="ioc-input" type="textarea" v-model="composeIoc.ioc"></b-input>
      </b-field>
      <b-field grouped>
        <b-field>
          <b-select placeholder="IOC type" v-model="composeIoc.type" label="IOC type" label-position="on-border">
            <option v-for="option in IOCTypes" :value="option.type" :key="option.type">
              {{ option.type }}
            </option>
          </b-select>
        </b-field>
        <b-field>
          <b-taginput
            v-model="editableTags"
            ellipsis
            icon="label"
            placeholder="Add a tag"
            aria-close-label="Delete this tag"
          >
          </b-taginput>
        </b-field>
        <b-field message="Readonly tags">
          <b-taginput readonly v-model="readonlyTags" ellipsis :closable="false" field="name" />
        </b-field>

        <b-field grouped expanded position="is-right">
          <p class="control">
            <b-button type="is-primary" @click="saveIoc">Save</b-button>
          </p>
          <p class="control">
            <b-button @click="$parent.close()">Cancel</b-button>
          </p>
        </b-field>
      </b-field>
      <b-field label="External reference (URI)">
        <b-input v-model="composeIoc.externalURI"></b-input>
      </b-field>
      <explore-preview
        style="margin-left: 10px"
        :searchQuery="generateOpenSearchQuery(composeIoc.ioc)['q']"
        :display-inline="true"
      ></explore-preview>
    </section>
  </div>
</template>

<script>
import { IOCTypes } from '@/utils/tagMetadata'
import ExplorePreview from '@/components/Common/ExplorePreview'

export default {
  components: { ExplorePreview },
  props: ['value'],
  data() {
    let newobj = JSON.parse(JSON.stringify(this.value))
    return {
      composeIoc: newobj,
      editableTags: newobj.tags.filter((tag) => typeof tag === 'string'),
      readonlyTags: newobj.tags.filter((tag) => typeof tag === 'object'),
      IOCTypes: IOCTypes,
    }
  },
  methods: {
    saveIoc() {
      this.$parent.close()
      this.composeIoc.tags = this.editableTags.concat(this.readonlyTags)
      this.$emit('input', this.composeIoc)
    },
    generateOpenSearchQuery(value, field) {
      if (value === undefined) {
        return { q: '' }
      }
      let query = `"${value}"`
      // Escape special OpenSearch characters: \, [space]
      query = query.replace(/[\\\s]/g, '\\$&')
      if (field !== undefined) {
        query = `${field}:${query}`
      }
      return { q: query }
    },
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
}
</script>

<style lang="scss">
.ioc-input {
  font-family: monospace;
}

.delete-ioc {
  cursor: pointer;
  color: #da1039;
}

.fa-question-circle {
  margin-left: 0.6em;
  opacity: 0.5;
}

.new-ioc i {
  margin-right: 0.5em;
}
.new-ioc {
  margin-left: 0.5em;
}
</style>
