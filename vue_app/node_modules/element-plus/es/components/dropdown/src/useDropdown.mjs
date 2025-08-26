import { inject, computed } from 'vue';
import { DROPDOWN_INSTANCE_INJECTION_KEY } from './tokens.mjs';

const useDropdown = () => {
  const elDropdown = inject(DROPDOWN_INSTANCE_INJECTION_KEY, {});
  const _elDropdownSize = computed(() => elDropdown == null ? void 0 : elDropdown.dropdownSize);
  return {
    elDropdown,
    _elDropdownSize
  };
};

export { useDropdown };
//# sourceMappingURL=useDropdown.mjs.map
