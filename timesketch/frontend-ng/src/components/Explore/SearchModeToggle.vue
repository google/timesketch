

<template>
  <!-- Which languages are on offer depends on the sketch and the cluster, so
       the menu opens only when there is more than query string to pick. -->
  <v-menu offset-y :disabled="!canOpenMenu">
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        depressed
        :color="$vuetify.theme.dark ? 'grey darken-3' : 'grey lighten-3'"
        v-bind="attrs"
        v-on="on"
        height="54"
        width="60"
        class="px-2 rounded-0 grey--text"
        :class="$vuetify.theme.dark ? 'text--lighten-3' : 'text--darken-3'"
        :title="!canOpenMenu ? 'This sketch does not support wildcard searches' : selectedTitle"
        :style="!canOpenMenu ? 'cursor: default; opacity: 0.8;' : ''"
      >
        {{ displayValue }}

        <v-icon v-if="canOpenMenu" small class="ml-1">
          mdi-chevron-down
        </v-icon>
      </v-btn>
    </template>

    <v-list two-line style="width: 360px;">
      <v-list-item
        v-for="item in menuItems"
        :key="item.value"
        @click="selectItem(item)"
      >
        <v-list-item-content>
          <v-list-item-title class="font-weight-bold">{{ item.title }}</v-list-item-title>
          <v-list-item-subtitle class="text-wrap mt-1 text--secondary" style="font-size: 0.8rem; line-height: 1.2;">
            {{ item.subtitle }}
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      default: 'query_string'
    },
    // Set when the cluster can serve PPL and SQL, which puts them in this
    // selector alongside the Lucene search modes. One control picks both the
    // language and the mode, so the two cannot disagree.
    directQueryEnabled: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      selectedValue: this.value,
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta || {};
    },
    isWildcardSupported() {
      return !!this.meta.supports_wildcard;
    },
    menuItems() {
      const items = [
        {
          title: 'Query String',
          subtitle: 'Standard Lucene query_string searching using tokenized and keyword type fields.',
          value: 'query_string'
        }
      ]
      // Wildcard needs string-type mappings on the sketch, and PPL and SQL
      // need the OpenSearch SQL plugin on the cluster, so the list cannot be
      // fixed at build time.
      if (this.isWildcardSupported) {
        items.push({
          title: 'Wildcard',
          subtitle: 'Exact-match substring searching on string type fields only. Use * or ? for wildcards.',
          value: 'wildcard'
        })
      }
      if (this.directQueryEnabled) {
        items.push({
          title: 'PPL',
          subtitle: 'OpenSearch Piped Processing Language. Runs directly against OpenSearch for aggregations and pipe-based queries.',
          value: 'ppl'
        })
        items.push({
          title: 'SQL',
          subtitle: 'OpenSearch SQL. Runs directly against OpenSearch using familiar SELECT / GROUP BY syntax.',
          value: 'sql'
        })
      }
      return items
    },
    canOpenMenu() {
      return this.menuItems.length > 1
    },
    selectedTitle() {
      const item = this.menuItems.find(i => i.value === this.selectedValue)
      return item ? item.title : ''
    },
    displayValue() {
      if (this.selectedValue === 'query_string') {
        return 'QS'
      }
      if (this.selectedValue === 'wildcard') {
        return 'WC'
      }
      if (this.selectedValue === 'ppl') {
        return 'PPL'
      }
      if (this.selectedValue === 'sql') {
        return 'SQL'
      }
      return this.selectedValue
    }
  },
  watch: {
    value(newVal) {
      this.selectedValue = newVal;
    },
    isWildcardSupported: {
      immediate: true,
      handler(supported) {
        // Only wildcard depends on the sketch's mappings, so only wildcard is
        // reset by losing them. PPL and SQL answer to the cluster instead.
        if (!supported && this.selectedValue === 'wildcard') {
          this.selectedValue = 'query_string';
          this.$emit('input', 'query_string');
        }
      }
    }
  },
  methods: {
    selectItem(item) {
      this.selectedValue = item.value;
      this.$emit('input', item.value);
    }
  }
}
</script>

<style scoped lang="scss">
</style>
