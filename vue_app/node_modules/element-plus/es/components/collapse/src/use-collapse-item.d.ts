import type { CollapseItemProps } from './collapse-item';
export declare const useCollapseItem: (props: CollapseItemProps) => {
    focusing: import("vue").Ref<boolean>;
    id: import("vue").ComputedRef<number>;
    isActive: import("vue").ComputedRef<boolean | undefined>;
    handleFocus: () => void;
    handleHeaderClick: (e: MouseEvent) => void;
    handleEnterClick: (e: KeyboardEvent) => void;
};
export declare const useCollapseItemDOM: (props: CollapseItemProps, { focusing, isActive, id }: Partial<ReturnType<typeof useCollapseItem>>) => {
    itemTitleKls: import("vue").ComputedRef<string[]>;
    arrowKls: import("vue").ComputedRef<string[]>;
    headKls: import("vue").ComputedRef<(string | {
        focusing: boolean | undefined;
    })[]>;
    rootKls: import("vue").ComputedRef<string[]>;
    itemWrapperKls: import("vue").ComputedRef<string>;
    itemContentKls: import("vue").ComputedRef<string>;
    scopedContentId: import("vue").ComputedRef<string>;
    scopedHeadId: import("vue").ComputedRef<string>;
};
