import { defineComponent, getCurrentInstance, useSlots, inject, ref, computed, watch, reactive, onBeforeUnmount, onBeforeUpdate, unref, withDirectives, openBlock, createElementBlock, normalizeClass, renderSlot, vShow, createCommentVNode } from 'vue';
import { eagerComputed } from '@vueuse/core';
import { tabsRootContextKey } from './constants.mjs';
import { tabPaneProps } from './tab-pane.mjs';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { throwError } from '../../../utils/error.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';

const COMPONENT_NAME = "ElTabPane";
const __default__ = defineComponent({
  name: COMPONENT_NAME
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: tabPaneProps,
  setup(__props) {
    const props = __props;
    const instance = getCurrentInstance();
    const slots = useSlots();
    const tabsRoot = inject(tabsRootContextKey);
    if (!tabsRoot)
      throwError(COMPONENT_NAME, "usage: <el-tabs><el-tab-pane /></el-tabs/>");
    const ns = useNamespace("tab-pane");
    const paneRef = ref();
    const index = ref();
    const isClosable = computed(() => props.closable || tabsRoot.props.closable);
    const active = eagerComputed(() => {
      var _a;
      return tabsRoot.currentName.value === ((_a = props.name) != null ? _a : index.value);
    });
    const loaded = ref(active.value);
    const paneName = computed(() => {
      var _a;
      return (_a = props.name) != null ? _a : index.value;
    });
    const shouldBeRender = eagerComputed(() => !props.lazy || loaded.value || active.value);
    const isFocusInsidePane = () => {
      var _a;
      return (_a = paneRef.value) == null ? void 0 : _a.contains(document.activeElement);
    };
    watch(active, (val) => {
      if (val)
        loaded.value = true;
    });
    const pane = reactive({
      uid: instance.uid,
      getVnode: () => instance.vnode,
      slots,
      props,
      paneName,
      active,
      index,
      isClosable,
      isFocusInsidePane
    });
    tabsRoot.registerPane(pane);
    onBeforeUnmount(() => {
      tabsRoot.unregisterPane(pane);
    });
    onBeforeUpdate(() => {
      var _a;
      if (slots.label)
        (_a = tabsRoot.nav$.value) == null ? void 0 : _a.scheduleRender();
    });
    return (_ctx, _cache) => {
      return unref(shouldBeRender) ? withDirectives((openBlock(), createElementBlock("div", {
        key: 0,
        id: `pane-${unref(paneName)}`,
        ref_key: "paneRef",
        ref: paneRef,
        class: normalizeClass(unref(ns).b()),
        role: "tabpanel",
        "aria-hidden": !unref(active),
        "aria-labelledby": `tab-${unref(paneName)}`
      }, [
        renderSlot(_ctx.$slots, "default")
      ], 10, ["id", "aria-hidden", "aria-labelledby"])), [
        [vShow, unref(active)]
      ]) : createCommentVNode("v-if", true);
    };
  }
});
var TabPane = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "tab-pane.vue"]]);

export { TabPane as default };
//# sourceMappingURL=tab-pane2.mjs.map
