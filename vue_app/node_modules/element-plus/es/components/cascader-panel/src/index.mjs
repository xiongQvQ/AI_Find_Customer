import { defineComponent, useSlots, ref, computed, provide, reactive, watch, onBeforeUpdate, onMounted, openBlock, createElementBlock, normalizeClass, unref, Fragment, renderList, createBlock, withCtx, renderSlot, nextTick } from 'vue';
import { isEqual, flattenDeep, cloneDeep } from 'lodash-unified';
import ElCascaderMenu from './menu.mjs';
import Store from './store.mjs';
import Node from './node.mjs';
import { cascaderPanelProps, cascaderPanelEmits, useCascaderConfig } from './config.mjs';
import { sortByOriginalOrder, checkNode, getMenuIndex } from './utils.mjs';
import { CASCADER_PANEL_INJECTION_KEY } from './types.mjs';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { unique, castArray } from '../../../utils/arrays.mjs';
import { scrollIntoView } from '../../../utils/dom/scroll.mjs';
import { focusNode, getSibling } from '../../../utils/dom/aria.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { UPDATE_MODEL_EVENT, CHANGE_EVENT } from '../../../constants/event.mjs';
import { isEmpty } from '../../../utils/types.mjs';
import { isClient } from '@vueuse/core';
import { EVENT_CODE } from '../../../constants/aria.mjs';

const __default__ = defineComponent({
  name: "ElCascaderPanel",
  inheritAttrs: false
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: cascaderPanelProps,
  emits: cascaderPanelEmits,
  setup(__props, { expose, emit }) {
    const props = __props;
    let manualChecked = false;
    const ns = useNamespace("cascader");
    const config = useCascaderConfig(props);
    const slots = useSlots();
    let store;
    const initialLoaded = ref(true);
    const menuList = ref([]);
    const checkedValue = ref();
    const menus = ref([]);
    const expandingNode = ref();
    const checkedNodes = ref([]);
    const isHoverMenu = computed(() => config.value.expandTrigger === "hover");
    const renderLabelFn = computed(() => props.renderLabel || slots.default);
    const initStore = () => {
      const { options } = props;
      const cfg = config.value;
      manualChecked = false;
      store = new Store(options, cfg);
      menus.value = [store.getNodes()];
      if (cfg.lazy && isEmpty(props.options)) {
        initialLoaded.value = false;
        lazyLoad(void 0, (list) => {
          if (list) {
            store = new Store(list, cfg);
            menus.value = [store.getNodes()];
          }
          initialLoaded.value = true;
          syncCheckedValue(false, true);
        });
      } else {
        syncCheckedValue(false, true);
      }
    };
    const lazyLoad = (node, cb) => {
      const cfg = config.value;
      node = node || new Node({}, cfg, void 0, true);
      node.loading = true;
      const resolve = (dataList) => {
        const _node = node;
        const parent = _node.root ? null : _node;
        _node.loading = false;
        _node.loaded = true;
        _node.childrenData = _node.childrenData || [];
        dataList && (store == null ? void 0 : store.appendNodes(dataList, parent));
        dataList && (cb == null ? void 0 : cb(dataList));
      };
      cfg.lazyLoad(node, resolve);
    };
    const expandNode = (node, silent) => {
      var _a;
      const { level } = node;
      const newMenus = menus.value.slice(0, level);
      let newExpandingNode;
      if (node.isLeaf) {
        newExpandingNode = node.pathNodes[level - 2];
      } else {
        newExpandingNode = node;
        newMenus.push(node.children);
      }
      if (((_a = expandingNode.value) == null ? void 0 : _a.uid) !== (newExpandingNode == null ? void 0 : newExpandingNode.uid)) {
        expandingNode.value = node;
        menus.value = newMenus;
        !silent && emit("expand-change", (node == null ? void 0 : node.pathValues) || []);
      }
    };
    const handleCheckChange = (node, checked, emitClose = true) => {
      const { checkStrictly, multiple } = config.value;
      const oldNode = checkedNodes.value[0];
      manualChecked = true;
      !multiple && (oldNode == null ? void 0 : oldNode.doCheck(false));
      node.doCheck(checked);
      calculateCheckedValue();
      emitClose && !multiple && !checkStrictly && emit("close");
      !emitClose && !multiple && !checkStrictly && expandParentNode(node);
    };
    const expandParentNode = (node) => {
      if (!node)
        return;
      node = node.parent;
      expandParentNode(node);
      node && expandNode(node);
    };
    const getFlattedNodes = (leafOnly) => store == null ? void 0 : store.getFlattedNodes(leafOnly);
    const getCheckedNodes = (leafOnly) => {
      var _a;
      return (_a = getFlattedNodes(leafOnly)) == null ? void 0 : _a.filter(({ checked }) => checked !== false);
    };
    const clearCheckedNodes = () => {
      checkedNodes.value.forEach((node) => node.doCheck(false));
      calculateCheckedValue();
      menus.value = menus.value.slice(0, 1);
      expandingNode.value = void 0;
      emit("expand-change", []);
    };
    const calculateCheckedValue = () => {
      var _a;
      const { checkStrictly, multiple } = config.value;
      const oldNodes = checkedNodes.value;
      const newNodes = getCheckedNodes(!checkStrictly);
      const nodes = sortByOriginalOrder(oldNodes, newNodes);
      const values = nodes.map((node) => node.valueByOption);
      checkedNodes.value = nodes;
      checkedValue.value = multiple ? values : (_a = values[0]) != null ? _a : null;
    };
    const syncCheckedValue = (loaded = false, forced = false) => {
      const { modelValue } = props;
      const { lazy, multiple, checkStrictly } = config.value;
      const leafOnly = !checkStrictly;
      if (!initialLoaded.value || manualChecked || !forced && isEqual(modelValue, checkedValue.value))
        return;
      if (lazy && !loaded) {
        const values = unique(flattenDeep(castArray(modelValue)));
        const nodes = values.map((val) => store == null ? void 0 : store.getNodeByValue(val)).filter((node) => !!node && !node.loaded && !node.loading);
        if (nodes.length) {
          nodes.forEach((node) => {
            lazyLoad(node, () => syncCheckedValue(false, forced));
          });
        } else {
          syncCheckedValue(true, forced);
        }
      } else {
        const values = multiple ? castArray(modelValue) : [modelValue];
        const nodes = unique(values.map((val) => store == null ? void 0 : store.getNodeByValue(val, leafOnly)));
        syncMenuState(nodes, forced);
        checkedValue.value = cloneDeep(modelValue != null ? modelValue : void 0);
      }
    };
    const syncMenuState = (newCheckedNodes, reserveExpandingState = true) => {
      const { checkStrictly } = config.value;
      const oldNodes = checkedNodes.value;
      const newNodes = newCheckedNodes.filter((node) => !!node && (checkStrictly || node.isLeaf));
      const oldExpandingNode = store == null ? void 0 : store.getSameNode(expandingNode.value);
      const newExpandingNode = reserveExpandingState && oldExpandingNode || newNodes[0];
      if (newExpandingNode) {
        newExpandingNode.pathNodes.forEach((node) => expandNode(node, true));
      } else {
        expandingNode.value = void 0;
      }
      oldNodes.forEach((node) => node.doCheck(false));
      reactive(newNodes).forEach((node) => node.doCheck(true));
      checkedNodes.value = newNodes;
      nextTick(scrollToExpandingNode);
    };
    const scrollToExpandingNode = () => {
      if (!isClient)
        return;
      menuList.value.forEach((menu) => {
        const menuElement = menu == null ? void 0 : menu.$el;
        if (menuElement) {
          const container = menuElement.querySelector(`.${ns.namespace.value}-scrollbar__wrap`);
          const activeNode = menuElement.querySelector(`.${ns.b("node")}.${ns.is("active")}:last-child`) || menuElement.querySelector(`.${ns.b("node")}.in-active-path`);
          scrollIntoView(container, activeNode);
        }
      });
    };
    const handleKeyDown = (e) => {
      const target = e.target;
      const { code } = e;
      switch (code) {
        case EVENT_CODE.up:
        case EVENT_CODE.down: {
          e.preventDefault();
          const distance = code === EVENT_CODE.up ? -1 : 1;
          focusNode(getSibling(target, distance, `.${ns.b("node")}[tabindex="-1"]`));
          break;
        }
        case EVENT_CODE.left: {
          e.preventDefault();
          const preMenu = menuList.value[getMenuIndex(target) - 1];
          const expandedNode = preMenu == null ? void 0 : preMenu.$el.querySelector(`.${ns.b("node")}[aria-expanded="true"]`);
          focusNode(expandedNode);
          break;
        }
        case EVENT_CODE.right: {
          e.preventDefault();
          const nextMenu = menuList.value[getMenuIndex(target) + 1];
          const firstNode = nextMenu == null ? void 0 : nextMenu.$el.querySelector(`.${ns.b("node")}[tabindex="-1"]`);
          focusNode(firstNode);
          break;
        }
        case EVENT_CODE.enter:
        case EVENT_CODE.numpadEnter:
          checkNode(target);
          break;
      }
    };
    provide(CASCADER_PANEL_INJECTION_KEY, reactive({
      config,
      expandingNode,
      checkedNodes,
      isHoverMenu,
      initialLoaded,
      renderLabelFn,
      lazyLoad,
      expandNode,
      handleCheckChange
    }));
    watch(config, (newVal, oldVal) => {
      if (isEqual(newVal, oldVal))
        return;
      initStore();
    }, {
      immediate: true
    });
    watch(() => props.options, initStore, {
      deep: true
    });
    watch(() => props.modelValue, () => {
      manualChecked = false;
      syncCheckedValue();
    }, {
      deep: true
    });
    watch(() => checkedValue.value, (val) => {
      if (!isEqual(val, props.modelValue)) {
        emit(UPDATE_MODEL_EVENT, val);
        emit(CHANGE_EVENT, val);
      }
    });
    onBeforeUpdate(() => menuList.value = []);
    onMounted(() => !isEmpty(props.modelValue) && syncCheckedValue());
    expose({
      menuList,
      menus,
      checkedNodes,
      handleKeyDown,
      handleCheckChange,
      getFlattedNodes,
      getCheckedNodes,
      clearCheckedNodes,
      calculateCheckedValue,
      scrollToExpandingNode
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        class: normalizeClass([unref(ns).b("panel"), unref(ns).is("bordered", _ctx.border)]),
        onKeydown: handleKeyDown
      }, [
        (openBlock(true), createElementBlock(Fragment, null, renderList(menus.value, (menu, index) => {
          return openBlock(), createBlock(ElCascaderMenu, {
            key: index,
            ref_for: true,
            ref: (item) => menuList.value[index] = item,
            index,
            nodes: [...menu]
          }, {
            empty: withCtx(() => [
              renderSlot(_ctx.$slots, "empty")
            ]),
            _: 2
          }, 1032, ["index", "nodes"]);
        }), 128))
      ], 34);
    };
  }
});
var CascaderPanel = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "index.vue"]]);

export { CascaderPanel as default };
//# sourceMappingURL=index.mjs.map
