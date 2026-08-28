declare module 'django-js-reverse' {
    export type UrlsFunction = {
        [routeName: string]: (...args: any[]) => string;
    };

    export default function djangoJsReverse(data: any): UrlsFunction;
}