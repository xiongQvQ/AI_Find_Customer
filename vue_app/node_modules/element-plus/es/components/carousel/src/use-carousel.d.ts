import type { SetupContext } from 'vue';
import type { CarouselItemContext } from './constants';
import type { CarouselEmits, CarouselProps } from './carousel';
export declare const useCarousel: (props: CarouselProps, emit: SetupContext<CarouselEmits>["emit"], componentName: string) => {
    root: import("vue").Ref<HTMLDivElement | undefined>;
    activeIndex: import("vue").Ref<number>;
    exposeActiveIndex: import("vue").WritableComputedRef<number>;
    arrowDisplay: import("vue").ComputedRef<boolean>;
    hasLabel: import("vue").ComputedRef<boolean>;
    hover: import("vue").Ref<boolean>;
    isCardType: import("vue").ComputedRef<boolean>;
    items: import("vue").ShallowRef<CarouselItemContext[]>;
    isVertical: import("vue").ComputedRef<boolean>;
    containerStyle: import("vue").ComputedRef<{
        height: string;
        overflow?: undefined;
    } | {
        height: string;
        overflow: string;
    }>;
    isItemsTwoLength: import("vue").Ref<boolean>;
    handleButtonEnter: (arrow: "left" | "right") => void;
    handleButtonLeave: () => void;
    handleIndicatorClick: (index: number) => void;
    handleMouseEnter: () => void;
    handleMouseLeave: () => void;
    setActiveItem: (index: number | string) => void;
    prev: () => void;
    next: () => void;
    PlaceholderItem: () => (import("element-plus/es/utils").VNodeChildAtom | {
        [name: string]: unknown;
        $stable?: boolean;
    })[] | null;
    isTwoLengthShow: (index: number) => boolean;
    ItemsSorter: import("vue").DefineComponent<{}, () => import("vue").VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }> | null, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, import("vue").EmitsOptions, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{}>>, {}>;
    throttledArrowClick: import("lodash").DebouncedFunc<(index: number) => void>;
    throttledIndicatorHover: import("lodash").DebouncedFunc<(index: number) => void>;
};
