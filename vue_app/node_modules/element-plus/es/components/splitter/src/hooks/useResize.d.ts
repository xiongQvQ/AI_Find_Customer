import type { ComputedRef, Ref } from 'vue';
import type { PanelItemState } from '../type';
export declare function useResize(panels: Ref<PanelItemState[]>, containerSize: ComputedRef<number>, pxSizes: ComputedRef<number[]>, lazy: Ref<boolean>): {
    lazyOffset: Ref<number>;
    onMoveStart: (index: number) => void;
    onMoving: (index: number, offset: number) => void;
    onMoveEnd: () => void;
    movingIndex: Ref<{
        index: number;
        confirmed: boolean;
    } | null>;
    onCollapse: (index: number, type: "start" | "end") => void;
};
