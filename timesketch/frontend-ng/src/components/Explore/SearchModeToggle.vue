

<template>
  <v-menu offset-y :disabled="!isWildcardSupported">
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
        :title="!isWildcardSupported ? 'This sketch does not support wildcard searches' : selectedTitle"
        :style="!isWildcardSupported ? 'cursor: default; opacity: 0.8;' : ''"
      >
        {{ displayValue }}

        <v-icon v-if="isWildcardSupported" small class="ml-1">
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
    }
  },
  data() {
    return {
      menuItems: [
        {
          title: 'Query String',
          subtitle: 'Standard Lucene query_string searching using tokenized and keyword type fields.',
          value: 'query_string'
        },
        {
          title: 'Wildcard',
          subtitle: 'Exact-match substring searching on string type fields only. Use * or ? for wildcards.',
          value: 'wildcard'
        }
      ],
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
        if (!supported && this.selectedValue !== 'query_string') {
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
