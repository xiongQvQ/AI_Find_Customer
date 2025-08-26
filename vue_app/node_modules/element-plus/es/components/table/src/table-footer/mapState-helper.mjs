import { inject, computed } from 'vue';
import { TABLE_INJECTION_KEY } from '../tokens.mjs';

function useMapState() {
  const table = inject(TABLE_INJECTION_KEY);
  const store = table == null ? void 0 : table.store;
  const leftFixedLeafCount = computed(() => {
    var _a;
    return (_a = store == null ? void 0 : store.states.fixedLeafColumnsLength.value) != null ? _a : 0;
  });
  const rightFixedLeafCount = computed(() => {
    var _a;
    return (_a = store == null ? void 0 : store.states.rightFixedColumns.value.length) != null ? _a : 0;
  });
  const columnsCount = computed(() => {
    var _a;
    return (_a = store == null ? void 0 : store.states.columns.value.length) != null ? _a : 0;
  });
  const leftFixedCount = computed(() => {
    var _a;
    return (_a = store == null ? void 0 : store.states.fixedColumns.value.length) != null ? _a : 0;
  });
  const rightFixedCount = computed(() => {
    var _a;
    return (_a = store == null ? void 0 : store.states.rightFixedColumns.value.length) != null ? _a : 0;
  });
  return {
    leftFixedLeafCount,
    rightFixedLeafCount,
    columnsCount,
    leftFixedCount,
    rightFixedCount,
    columns: computed(() => {
      var _a;
      return (_a = store == null ? void 0 : store.states.columns.value) != null ? _a : [];
    })
  };
}

export { useMapState as default };
//# sourceMappingURL=mapState-helper.mjs.map
