import type { Ref } from 'vue';
export declare function useContainer(layout: Ref<'horizontal' | 'vertical'>): {
    containerEl: Ref<HTMLDivElement | undefined>;
    containerSize: import("vue").ComputedRef<number>;
};
