import { ref, isRef } from 'vue';
import Loading from './service.mjs';
import { isObject, hyphenate, isString } from '@vue/shared';

const INSTANCE_KEY = Symbol("ElLoading");
const getAttributeName = (name) => {
  return `element-loading-${hyphenate(name)}`;
};
const createInstance = (el, binding) => {
  var _a, _b, _c, _d;
  const vm = binding.instance;
  const getBindingProp = (key) => isObject(binding.value) ? binding.value[key] : void 0;
  const resolveExpression = (key) => {
    const data = isString(key) && (vm == null ? void 0 : vm[key]) || key;
    return ref(data);
  };
  const getProp = (name) => resolveExpression(getBindingProp(name) || el.getAttribute(getAttributeName(name)));
  const fullscreen = (_a = getBindingProp("fullscreen")) != null ? _a : binding.modifiers.fullscreen;
  const options = {
    text: getProp("text"),
    svg: getProp("svg"),
    svgViewBox: getProp("svgViewBox"),
    spinner: getProp("spinner"),
    background: getProp("background"),
    customClass: getProp("customClass"),
    fullscreen,
    target: (_b = getBindingProp("target")) != null ? _b : fullscreen ? void 0 : el,
    body: (_c = getBindingProp("body")) != null ? _c : binding.modifiers.body,
    lock: (_d = getBindingProp("lock")) != null ? _d : binding.modifiers.lock
  };
  const instance = Loading(options);
  instance._context = vLoading._context;
  el[INSTANCE_KEY] = {
    options,
    instance
  };
};
const updateOptions = (originalOptions, newOptions) => {
  for (const key of Object.keys(originalOptions)) {
    if (isRef(originalOptions[key]))
      originalOptions[key].value = newOptions[key];
  }
};
const vLoading = {
  mounted(el, binding) {
    if (binding.value) {
      createInstance(el, binding);
    }
  },
  updated(el, binding) {
    const instance = el[INSTANCE_KEY];
    if (!binding.value) {
      instance == null ? void 0 : instance.instance.close();
      el[INSTANCE_KEY] = null;
      return;
    }
    if (!instance)
      createInstance(el, binding);
    else {
      updateOptions(instance.options, isObject(binding.value) ? binding.value : {
        text: el.getAttribute(getAttributeName("text")),
        svg: el.getAttribute(getAttributeName("svg")),
        svgViewBox: el.getAttribute(getAttributeName("svgViewBox")),
        spinner: el.getAttribute(getAttributeName("spinner")),
        background: el.getAttribute(getAttributeName("background")),
        customClass: el.getAttribute(getAttributeName("customClass"))
      });
    }
  },
  unmounted(el) {
    var _a;
    (_a = el[INSTANCE_KEY]) == null ? void 0 : _a.instance.close();
    el[INSTANCE_KEY] = null;
  }
};
vLoading._context = null;

export { vLoading as default };
//# sourceMappingURL=directive.mjs.map
