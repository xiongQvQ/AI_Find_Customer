import type { OptionV2EmitFn, OptionV2Props } from './defaults';
export declare function useOption(props: OptionV2Props, { emit }: {
    emit: OptionV2EmitFn;
}): {
    hoverItem: () => void;
    selectOptionClick: () => void;
};
