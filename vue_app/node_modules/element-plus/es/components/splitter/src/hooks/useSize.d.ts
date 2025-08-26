import type { ComputedRef, Ref } from 'vue';
import type { PanelItemState } from '../type';
export declare function getPct(str: string): number;
export declare function getPx(str: string): number;
export declare function isPct(itemSize: string | number | undefined): itemSize is string;
export declare function isPx(itemSize: string | number | undefined): itemSize is string;
export declare function useSize(panels: Ref<PanelItemState[]>, containerSize: ComputedRef<number>): {
    percentSizes: Ref<number[]>;
    pxSizes: ComputedRef<number[]>;
};
