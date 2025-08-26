import { defineComponent, watch, renderSlot } from 'vue';
import { provideGlobalConfig } from './hooks/use-global-config.mjs';
import { configProviderProps } from './config-provider-props.mjs';

const messageConfig = {
  placement: "top"
};
const ConfigProvider = defineComponent({
  name: "ElConfigProvider",
  props: configProviderProps,
  setup(props, { slots }) {
    const config = provideGlobalConfig(props);
    watch(() => props.message, (val) => {
      var _a, _b;
      Object.assign(messageConfig, (_b = (_a = config == null ? void 0 : config.value) == null ? void 0 : _a.message) != null ? _b : {}, val != null ? val : {});
    }, { immediate: true, deep: true });
    return () => renderSlot(slots, "default", { config: config == null ? void 0 : config.value });
  }
});

export { ConfigProvider as default, messageConfig };
//# sourceMappingURL=config-provider.mjs.map
