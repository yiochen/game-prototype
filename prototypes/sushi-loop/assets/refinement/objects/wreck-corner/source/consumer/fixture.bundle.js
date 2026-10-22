var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __commonJS = (cb, mod) => function __require() {
  try {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  } catch (e) {
    throw mod = 0, e;
  }
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// ../../../../dev/game-prototype/node_modules/react/cjs/react.production.js
var require_react_production = __commonJS({
  "../../../../dev/game-prototype/node_modules/react/cjs/react.production.js"(exports) {
    "use strict";
    var REACT_ELEMENT_TYPE = /* @__PURE__ */ Symbol.for("react.transitional.element");
    var REACT_PORTAL_TYPE = /* @__PURE__ */ Symbol.for("react.portal");
    var REACT_FRAGMENT_TYPE = /* @__PURE__ */ Symbol.for("react.fragment");
    var REACT_STRICT_MODE_TYPE = /* @__PURE__ */ Symbol.for("react.strict_mode");
    var REACT_PROFILER_TYPE = /* @__PURE__ */ Symbol.for("react.profiler");
    var REACT_CONSUMER_TYPE = /* @__PURE__ */ Symbol.for("react.consumer");
    var REACT_CONTEXT_TYPE = /* @__PURE__ */ Symbol.for("react.context");
    var REACT_FORWARD_REF_TYPE = /* @__PURE__ */ Symbol.for("react.forward_ref");
    var REACT_SUSPENSE_TYPE = /* @__PURE__ */ Symbol.for("react.suspense");
    var REACT_MEMO_TYPE = /* @__PURE__ */ Symbol.for("react.memo");
    var REACT_LAZY_TYPE = /* @__PURE__ */ Symbol.for("react.lazy");
    var REACT_ACTIVITY_TYPE = /* @__PURE__ */ Symbol.for("react.activity");
    var REACT_VIEW_TRANSITION_TYPE = /* @__PURE__ */ Symbol.for("react.view_transition");
    var MAYBE_ITERATOR_SYMBOL = Symbol.iterator;
    function getIteratorFn(maybeIterable) {
      if (null === maybeIterable || "object" !== typeof maybeIterable) return null;
      maybeIterable = MAYBE_ITERATOR_SYMBOL && maybeIterable[MAYBE_ITERATOR_SYMBOL] || maybeIterable["@@iterator"];
      return "function" === typeof maybeIterable ? maybeIterable : null;
    }
    var ReactNoopUpdateQueue = {
      isMounted: function() {
        return false;
      },
      enqueueForceUpdate: function() {
      },
      enqueueReplaceState: function() {
      },
      enqueueSetState: function() {
      }
    };
    var assign = Object.assign;
    var emptyObject = {};
    function Component(props, context, updater) {
      this.props = props;
      this.context = context;
      this.refs = emptyObject;
      this.updater = updater || ReactNoopUpdateQueue;
    }
    Component.prototype.isReactComponent = {};
    Component.prototype.setState = function(partialState, callback) {
      if ("object" !== typeof partialState && "function" !== typeof partialState && null != partialState)
        throw Error(
          "takes an object of state variables to update or a function which returns an object of state variables."
        );
      this.updater.enqueueSetState(this, partialState, callback, "setState");
    };
    Component.prototype.forceUpdate = function(callback) {
      this.updater.enqueueForceUpdate(this, callback, "forceUpdate");
    };
    function ComponentDummy() {
    }
    ComponentDummy.prototype = Component.prototype;
    function PureComponent(props, context, updater) {
      this.props = props;
      this.context = context;
      this.refs = emptyObject;
      this.updater = updater || ReactNoopUpdateQueue;
    }
    var pureComponentPrototype = PureComponent.prototype = new ComponentDummy();
    pureComponentPrototype.constructor = PureComponent;
    assign(pureComponentPrototype, Component.prototype);
    pureComponentPrototype.isPureReactComponent = true;
    var isArrayImpl = Array.isArray;
    function noop() {
    }
    var ReactSharedInternals = { H: null, A: null, T: null, S: null };
    var hasOwnProperty = Object.prototype.hasOwnProperty;
    function ReactElement(type, key, props) {
      var refProp = props.ref;
      return {
        $$typeof: REACT_ELEMENT_TYPE,
        type,
        key,
        ref: void 0 !== refProp ? refProp : null,
        props
      };
    }
    function cloneAndReplaceKey(oldElement, newKey) {
      return ReactElement(oldElement.type, newKey, oldElement.props);
    }
    function isValidElement(object) {
      return "object" === typeof object && null !== object && object.$$typeof === REACT_ELEMENT_TYPE;
    }
    function escape(key) {
      var escaperLookup = { "=": "=0", ":": "=2" };
      return "$" + key.replace(/[=:]/g, function(match) {
        return escaperLookup[match];
      });
    }
    var userProvidedKeyEscapeRegex = /\/+/g;
    function getElementKey(element, index) {
      return "object" === typeof element && null !== element && null != element.key ? escape("" + element.key) : index.toString(36);
    }
    function resolveThenable(thenable) {
      switch (thenable.status) {
        case "fulfilled":
          return thenable.value;
        case "rejected":
          throw thenable.reason;
        default:
          switch ("string" === typeof thenable.status ? thenable.then(noop, noop) : (thenable.status = "pending", thenable.then(
            function(fulfilledValue) {
              "pending" === thenable.status && (thenable.status = "fulfilled", thenable.value = fulfilledValue);
            },
            function(error) {
              "pending" === thenable.status && (thenable.status = "rejected", thenable.reason = error);
            }
          )), thenable.status) {
            case "fulfilled":
              return thenable.value;
            case "rejected":
              throw thenable.reason;
          }
      }
      throw thenable;
    }
    function mapIntoArray(children, array, escapedPrefix, nameSoFar, callback) {
      var type = typeof children;
      if ("undefined" === type || "boolean" === type) children = null;
      var invokeCallback = false;
      if (null === children) invokeCallback = true;
      else
        switch (type) {
          case "bigint":
          case "string":
          case "number":
            invokeCallback = true;
            break;
          case "object":
            switch (children.$$typeof) {
              case REACT_ELEMENT_TYPE:
              case REACT_PORTAL_TYPE:
                invokeCallback = true;
                break;
              case REACT_LAZY_TYPE:
                return invokeCallback = children._init, mapIntoArray(
                  invokeCallback(children._payload),
                  array,
                  escapedPrefix,
                  nameSoFar,
                  callback
                );
            }
        }
      if (invokeCallback)
        return callback = callback(children), invokeCallback = "" === nameSoFar ? "." + getElementKey(children, 0) : nameSoFar, isArrayImpl(callback) ? (escapedPrefix = "", null != invokeCallback && (escapedPrefix = invokeCallback.replace(userProvidedKeyEscapeRegex, "$&/") + "/"), mapIntoArray(callback, array, escapedPrefix, "", function(c2) {
          return c2;
        })) : null != callback && (isValidElement(callback) && (callback = cloneAndReplaceKey(
          callback,
          escapedPrefix + (null == callback.key || children && children.key === callback.key ? "" : ("" + callback.key).replace(
            userProvidedKeyEscapeRegex,
            "$&/"
          ) + "/") + invokeCallback
        )), array.push(callback)), 1;
      invokeCallback = 0;
      var nextNamePrefix = "" === nameSoFar ? "." : nameSoFar + ":";
      if (isArrayImpl(children))
        for (var i = 0; i < children.length; i++)
          nameSoFar = children[i], type = nextNamePrefix + getElementKey(nameSoFar, i), invokeCallback += mapIntoArray(
            nameSoFar,
            array,
            escapedPrefix,
            type,
            callback
          );
      else if (i = getIteratorFn(children), "function" === typeof i)
        for (children = i.call(children), i = 0; !(nameSoFar = children.next()).done; )
          nameSoFar = nameSoFar.value, type = nextNamePrefix + getElementKey(nameSoFar, i++), invokeCallback += mapIntoArray(
            nameSoFar,
            array,
            escapedPrefix,
            type,
            callback
          );
      else if ("object" === type) {
        if ("function" === typeof children.then)
          return mapIntoArray(
            resolveThenable(children),
            array,
            escapedPrefix,
            nameSoFar,
            callback
          );
        array = String(children);
        throw Error(
          "Objects are not valid as a React child (found: " + ("[object Object]" === array ? "object with keys {" + Object.keys(children).join(", ") + "}" : array) + "). If you meant to render a collection of children, use an array instead."
        );
      }
      return invokeCallback;
    }
    function mapChildren(children, func, context) {
      if (null == children) return children;
      var result = [], count = 0;
      mapIntoArray(children, result, "", "", function(child) {
        return func.call(context, child, count++);
      });
      return result;
    }
    function lazyInitializer(payload) {
      if (-1 === payload._status) {
        var ctor = payload._result, thenable = ctor();
        thenable.then(
          function(moduleObject) {
            if (0 === payload._status || -1 === payload._status)
              payload._status = 1, payload._result = moduleObject, void 0 === thenable.status && (thenable.status = "fulfilled", thenable.value = moduleObject);
          },
          function(error) {
            if (0 === payload._status || -1 === payload._status)
              payload._status = 2, payload._result = error, void 0 === thenable.status && (thenable.status = "rejected", thenable.reason = error);
          }
        );
        -1 === payload._status && (payload._status = 0, payload._result = thenable);
      }
      if (1 === payload._status) return payload._result.default;
      throw payload._result;
    }
    var reportGlobalError = "function" === typeof reportError ? reportError : function(error) {
      if ("object" === typeof window && "function" === typeof window.ErrorEvent) {
        var event = new window.ErrorEvent("error", {
          bubbles: true,
          cancelable: true,
          message: "object" === typeof error && null !== error && "string" === typeof error.message ? String(error.message) : String(error),
          error
        });
        if (!window.dispatchEvent(event)) return;
      } else if ("object" === typeof process && "function" === typeof process.emit) {
        process.emit("uncaughtException", error);
        return;
      }
      console.error(error);
    };
    function startTransition(scope) {
      var prevTransition = ReactSharedInternals.T, currentTransition = {};
      currentTransition.types = null !== prevTransition ? prevTransition.types : null;
      ReactSharedInternals.T = currentTransition;
      try {
        var returnValue = scope(), onStartTransitionFinish = ReactSharedInternals.S;
        null !== onStartTransitionFinish && onStartTransitionFinish(currentTransition, returnValue);
        "object" === typeof returnValue && null !== returnValue && "function" === typeof returnValue.then && returnValue.then(noop, reportGlobalError);
      } catch (error) {
        reportGlobalError(error);
      } finally {
        null !== prevTransition && null !== currentTransition.types && (prevTransition.types = currentTransition.types), ReactSharedInternals.T = prevTransition;
      }
    }
    function addTransitionType(type) {
      var transition = ReactSharedInternals.T;
      if (null !== transition) {
        var transitionTypes = transition.types;
        null === transitionTypes ? transition.types = [type] : -1 === transitionTypes.indexOf(type) && transitionTypes.push(type);
      } else startTransition(addTransitionType.bind(null, type));
    }
    var Children = {
      map: mapChildren,
      forEach: function(children, forEachFunc, forEachContext) {
        mapChildren(
          children,
          function() {
            forEachFunc.apply(this, arguments);
          },
          forEachContext
        );
      },
      count: function(children) {
        var n = 0;
        mapChildren(children, function() {
          n++;
        });
        return n;
      },
      toArray: function(children) {
        return mapChildren(children, function(child) {
          return child;
        }) || [];
      },
      only: function(children) {
        if (!isValidElement(children))
          throw Error(
            "React.Children.only expected to receive a single React element child."
          );
        return children;
      }
    };
    exports.Activity = REACT_ACTIVITY_TYPE;
    exports.Children = Children;
    exports.Component = Component;
    exports.Fragment = REACT_FRAGMENT_TYPE;
    exports.Profiler = REACT_PROFILER_TYPE;
    exports.PureComponent = PureComponent;
    exports.StrictMode = REACT_STRICT_MODE_TYPE;
    exports.Suspense = REACT_SUSPENSE_TYPE;
    exports.ViewTransition = REACT_VIEW_TRANSITION_TYPE;
    exports.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = ReactSharedInternals;
    exports.__COMPILER_RUNTIME = {
      __proto__: null,
      c: function(size) {
        return ReactSharedInternals.H.useMemoCache(size);
      }
    };
    exports.addTransitionType = addTransitionType;
    exports.cache = function(fn) {
      return function() {
        return fn.apply(null, arguments);
      };
    };
    exports.cacheSignal = function() {
      return null;
    };
    exports.cloneElement = function(element, config, children) {
      if (null === element || void 0 === element)
        throw Error(
          "The argument must be a React element, but you passed " + element + "."
        );
      var props = assign({}, element.props), key = element.key;
      if (null != config)
        for (propName in void 0 !== config.key && (key = "" + config.key), config)
          !hasOwnProperty.call(config, propName) || "key" === propName || "__self" === propName || "__source" === propName || "ref" === propName && void 0 === config.ref || (props[propName] = config[propName]);
      var propName = arguments.length - 2;
      if (1 === propName) props.children = children;
      else if (1 < propName) {
        for (var childArray = Array(propName), i = 0; i < propName; i++)
          childArray[i] = arguments[i + 2];
        props.children = childArray;
      }
      return ReactElement(element.type, key, props);
    };
    exports.createContext = function(defaultValue) {
      defaultValue = {
        $$typeof: REACT_CONTEXT_TYPE,
        _currentValue: defaultValue,
        _currentValue2: defaultValue,
        _threadCount: 0,
        Provider: null,
        Consumer: null
      };
      defaultValue.Provider = defaultValue;
      defaultValue.Consumer = {
        $$typeof: REACT_CONSUMER_TYPE,
        _context: defaultValue
      };
      return defaultValue;
    };
    exports.createElement = function(type, config, children) {
      var propName, props = {}, key = null;
      if (null != config)
        for (propName in void 0 !== config.key && (key = "" + config.key), config)
          hasOwnProperty.call(config, propName) && "key" !== propName && "__self" !== propName && "__source" !== propName && (props[propName] = config[propName]);
      var childrenLength = arguments.length - 2;
      if (1 === childrenLength) props.children = children;
      else if (1 < childrenLength) {
        for (var childArray = Array(childrenLength), i = 0; i < childrenLength; i++)
          childArray[i] = arguments[i + 2];
        props.children = childArray;
      }
      if (type && type.defaultProps)
        for (propName in childrenLength = type.defaultProps, childrenLength)
          void 0 === props[propName] && (props[propName] = childrenLength[propName]);
      return ReactElement(type, key, props);
    };
    exports.createRef = function() {
      return { current: null };
    };
    exports.forwardRef = function(render) {
      return { $$typeof: REACT_FORWARD_REF_TYPE, render };
    };
    exports.isValidElement = isValidElement;
    exports.lazy = function(ctor) {
      return {
        $$typeof: REACT_LAZY_TYPE,
        _payload: { _status: -1, _result: ctor },
        _init: lazyInitializer
      };
    };
    exports.memo = function(type, compare) {
      return {
        $$typeof: REACT_MEMO_TYPE,
        type,
        compare: void 0 === compare ? null : compare
      };
    };
    exports.startTransition = startTransition;
    exports.unstable_useCacheRefresh = function() {
      return ReactSharedInternals.H.useCacheRefresh();
    };
    exports.use = function(usable) {
      return ReactSharedInternals.H.use(usable);
    };
    exports.useActionState = function(action, initialState, permalink) {
      return ReactSharedInternals.H.useActionState(action, initialState, permalink);
    };
    exports.useCallback = function(callback, deps) {
      return ReactSharedInternals.H.useCallback(callback, deps);
    };
    exports.useContext = function(Context) {
      return ReactSharedInternals.H.useContext(Context);
    };
    exports.useDebugValue = function() {
    };
    exports.useDeferredValue = function(value, initialValue) {
      return ReactSharedInternals.H.useDeferredValue(value, initialValue);
    };
    exports.useEffect = function(create, deps) {
      return ReactSharedInternals.H.useEffect(create, deps);
    };
    exports.useEffectEvent = function(callback) {
      return ReactSharedInternals.H.useEffectEvent(callback);
    };
    exports.useId = function() {
      return ReactSharedInternals.H.useId();
    };
    exports.useImperativeHandle = function(ref, create, deps) {
      return ReactSharedInternals.H.useImperativeHandle(ref, create, deps);
    };
    exports.useInsertionEffect = function(create, deps) {
      return ReactSharedInternals.H.useInsertionEffect(create, deps);
    };
    exports.useLayoutEffect = function(create, deps) {
      return ReactSharedInternals.H.useLayoutEffect(create, deps);
    };
    exports.useMemo = function(create, deps) {
      return ReactSharedInternals.H.useMemo(create, deps);
    };
    exports.useOptimistic = function(passthrough, reducer) {
      return ReactSharedInternals.H.useOptimistic(passthrough, reducer);
    };
    exports.useReducer = function(reducer, initialArg, init) {
      return ReactSharedInternals.H.useReducer(reducer, initialArg, init);
    };
    exports.useRef = function(initialValue) {
      return ReactSharedInternals.H.useRef(initialValue);
    };
    exports.useState = function(initialState) {
      return ReactSharedInternals.H.useState(initialState);
    };
    exports.useSyncExternalStore = function(subscribe, getSnapshot, getServerSnapshot) {
      return ReactSharedInternals.H.useSyncExternalStore(
        subscribe,
        getSnapshot,
        getServerSnapshot
      );
    };
    exports.useTransition = function() {
      return ReactSharedInternals.H.useTransition();
    };
    exports.version = "19.3.0";
  }
});

// ../../../../dev/game-prototype/node_modules/react/index.js
var require_react = __commonJS({
  "../../../../dev/game-prototype/node_modules/react/index.js"(exports, module) {
    "use strict";
    if (true) {
      module.exports = require_react_production();
    } else {
      module.exports = null;
    }
  }
});

// prototypes/sushi-loop/assets/refinement/objects/wreck-corner/source/consumer/world-sprite-raster.js
var import_react = __toESM(require_react(), 1);
function worldRasterPlan(sprites, bounds) {
  const scale = Math.max(1, ...sprites.map((sprite) => Math.max(sprite.rect[2] / sprite.width, sprite.rect[3] / sprite.height)));
  const x = (Math.floor(bounds[0] * scale) - 1) / scale;
  const y = (Math.floor(bounds[1] * scale) - 1) / scale;
  const width = Math.ceil((bounds[0] + bounds[2] - x) * scale) + 1;
  const height = Math.ceil((bounds[1] + bounds[3] - y) * scale) + 1;
  return { x, y, width, height, scale, sprites };
}
var rasterLayers = /* @__PURE__ */ new WeakMap();
function paintWorldRaster(canvas, plan, loadedImages) {
  if (canvas.width !== plan.width) canvas.width = plan.width;
  if (canvas.height !== plan.height) canvas.height = plan.height;
  const context = canvas.getContext("2d");
  context.imageSmoothingEnabled = false;
  context.clearRect(0, 0, canvas.width, canvas.height);
  const position = (sprite) => [(sprite.x - plan.x) * plan.scale, (sprite.y - plan.y) * plan.scale];
  const integral = (value) => Math.abs(value - Math.round(value)) <= Number.EPSILON * Math.max(1, Math.abs(value)) * 8;
  for (let index = 0; index < plan.sprites.length; ) {
    const sprite = plan.sprites[index];
    const [x, y] = position(sprite);
    const width = sprite.width * plan.scale, height = sprite.height * plan.scale;
    const group = [{ index, x: 0, y: 0, width, height }];
    let end = index + 1, left = 0, top = 0, right = width, bottom = height;
    if (integral(width) && integral(height)) {
      while (end < plan.sprites.length) {
        const next2 = plan.sprites[end], [nextX, nextY] = position(next2);
        const dx = nextX - x, dy = nextY - y;
        const nextWidth = next2.width * plan.scale, nextHeight = next2.height * plan.scale;
        if (![dx, dy, nextWidth, nextHeight].every(integral)) break;
        const gx = Math.round(dx), gy = Math.round(dy);
        group.push({ index: end, x: gx, y: gy, width: Math.round(nextWidth), height: Math.round(nextHeight) });
        left = Math.min(left, gx);
        top = Math.min(top, gy);
        right = Math.max(right, gx + Math.round(nextWidth));
        bottom = Math.max(bottom, gy + Math.round(nextHeight));
        end++;
      }
    }
    if (group.length === 1 || integral(x) && integral(y)) {
      for (const item of group) {
        const current = plan.sprites[item.index], [dx, dy] = position(current);
        context.drawImage(
          loadedImages[item.index],
          ...current.rect,
          dx,
          dy,
          current.width * plan.scale,
          current.height * plan.scale
        );
      }
    } else {
      let layer = rasterLayers.get(canvas);
      if (!layer) {
        layer = canvas.ownerDocument.createElement("canvas");
        rasterLayers.set(canvas, layer);
      }
      if (layer.width !== right - left) layer.width = right - left;
      if (layer.height !== bottom - top) layer.height = bottom - top;
      const layerContext = layer.getContext("2d");
      layerContext.imageSmoothingEnabled = false;
      layerContext.clearRect(0, 0, layer.width, layer.height);
      for (const item of group) layerContext.drawImage(
        loadedImages[item.index],
        ...plan.sprites[item.index].rect,
        item.x - left,
        item.y - top,
        item.width,
        item.height
      );
      context.drawImage(layer, x + left, y + top);
    }
    index = end;
  }
}

// prototypes/sushi-loop/assets/refinement/objects/wreck-corner/source/consumer/sprite-layout.js
var positive = (value, fallback) => Number.isFinite(Number(value)) && Number(value) > 0 ? Number(value) : fallback;
function spriteFrame(object, clip, direction, seconds = 0) {
  const entry = clip?.directions?.[direction];
  if (!entry?.image) return null;
  const frameSize = entry.frameSize || clip.frameSize || object.frameSize || [192, 320];
  const root = entry.root || clip.root || object.root || [96, 248];
  const sourceScale = positive(entry.sourceScale ?? clip.sourceScale ?? object.sourceScale, 1);
  const frames = Math.max(1, Math.floor(positive(entry.frames ?? clip.frames, 1)));
  const fps = positive(clip.fps, 12);
  const rawFrame = Math.max(0, Math.floor(Math.max(0, seconds) * fps + 1e-7));
  const frame = clip.loop === false ? Math.min(frames - 1, rawFrame) : rawFrame % frames;
  const offset = Math.max(0, Math.floor(Number(entry.offset) || 0));
  const columns = Math.max(1, Math.floor(positive(entry.columns, frames)));
  const rows = Math.max(1, Math.floor(positive(entry.rows, Math.ceil((frames + offset) / columns))));
  const [width, height] = frameSize;
  const rect = entry.rects?.[frame] || [(offset + frame) % columns * width * sourceScale, Math.floor((offset + frame) / columns) * height * sourceScale, width * sourceScale, height * sourceScale];
  return { image: entry.image, frame, frames, frameSize, root, rect, atlasSize: entry.atlasSize || [width * sourceScale * columns, height * sourceScale * rows] };
}
function orderPlacements(placements, objects) {
  const get2 = (placement) => objects.find((object) => object.id === placement.object);
  const pass = (placement) => {
    const object = get2(placement) || {};
    const value = placement.renderPass || object.renderPass || (object.kind === "floor" ? "background" : "world");
    return value === "background" ? 0 : ["foreground", "overhead", "overlay"].includes(value) ? 2 : 1;
  };
  const ordered = placements.map((placement, index) => ({ ...placement, _index: index })).sort((a, b) => {
    const rank = (placement) => placement.layer ?? get2(placement)?.layer ?? (get2(placement)?.kind === "floor" ? 0 : get2(placement)?.kind === "belt" ? 1 : 2);
    const depth = (placement) => {
      const object = get2(placement) || {};
      const footprint = footprintFor(object, placement.direction);
      const rootCell = object.directionRootCells?.[placement.direction || "S"] || object.rootCell || [footprint[0] / 2, footprint[1] / 2];
      return placement.y + rootCell[1];
    };
    return pass(a) - pass(b) || depth(a) - depth(b) || rank(a) - rank(b) || a._index - b._index;
  });
  if (!ordered.some((placement) => placement.supportedBy)) return ordered;
  const supports = /* @__PURE__ */ new Map();
  for (const placement of ordered) {
    if (!placement.supportedBy) continue;
    const named = ordered.filter((candidate) => candidate.id === placement.supportedBy);
    const matches = named.length ? named : ordered.filter((candidate) => candidate.object === placement.supportedBy);
    if (matches.length !== 1 || matches[0] === placement) throw new Error(`Invalid or ambiguous sprite support: ${placement.supportedBy}`);
    if (pass(matches[0]) > pass(placement)) throw new Error("Sprite support cannot override a later render pass");
    supports.set(placement, matches[0]);
  }
  const result = [], remaining = new Set(ordered);
  while (remaining.size) {
    const next2 = ordered.find((placement) => remaining.has(placement) && !remaining.has(supports.get(placement)));
    if (!next2) throw new Error("Cyclic sprite support relationships");
    result.push(next2);
    remaining.delete(next2);
  }
  return result;
}
function groundRoot(placement, object, cellSize = 128) {
  const footprint = footprintFor(object, placement.direction);
  const rootCell = object.directionRootCells?.[placement.direction || "S"] || object.rootCell || [footprint[0] / 2, footprint[1] / 2];
  return [(placement.x + rootCell[0]) * cellSize + (placement.offset?.[0] || 0) + (placement.supportOffset?.[0] || 0), (placement.y + rootCell[1]) * cellSize + (placement.offset?.[1] || 0) + (placement.supportOffset?.[1] || 0)];
}
function footprintFor(object, direction = "S") {
  return object.directionFootprints?.[direction] || object.footprint || [1, 1];
}

// prototypes/sushi-loop/assets/refinement/objects/wreck-corner/source/consumer/fixture.mjs
var get = async (u) => await (await fetch(u)).json();
var original = await get("../resources/catalog-object.json");
var middle = await get("../resources/wreck-middle-catalog.json");
var edge = await get("../resources/wreck-edge-catalog.json");
var captures = await get("../../candidates/round-01/capture-records.json");
var cases = [{ id: "logical128-integer", cssScale: 1, rootOffset: [0, 0], pan: [0, 0] }, { id: "logical128-fractional", cssScale: 0.773, rootOffset: [0.375, 0.625], pan: [0.213, -0.371] }, { id: "phone32-integer", cssScale: 0.25, rootOffset: [0, 0], pan: [0, 0] }, { id: "phone32-fractional", cssScale: 0.25, rootOffset: [0.375, 0.625], pan: [0.213, -0.371] }];
var c = cases.find((c2) => c2.id === new URLSearchParams(location.search).get("case"));
window.evidence = { case: c, actualDPR: devicePixelRatio, fixtures: [] };
window.nativeCanvasPNGs = [];
var image = (url) => new Promise((yes, no) => {
  const i = new Image();
  i.onload = () => yes(i);
  i.onerror = no;
  i.src = url;
});
var next = { S: "E", E: "N", N: "W", W: "S" };
for (const o of [original, middle, edge]) for (const d of ["N", "E", "S", "W"]) o.clips[0].directions[d].image = o === original ? "../../candidates/round-01/atlases/static-" + d + ".png" : "../resources/" + o.id + "/" + d + ".png";
for (const kind of ["middle-L", "mixed-edge-L"]) for (const d of ["N", "E", "S", "W"]) {
  const record = captures.records.find((r) => r.path === kind + "/" + d + ".png"), size = record.camera.frame, origin = record.camera.root, roots = record.assembly.roots;
  const west = kind === "middle-L" ? middle : edge, objects = [original, middle, edge];
  const placements = [{ id: kind + "-corner-" + d, object: original.id, direction: d, x: -0.5, y: -0.5, offset: c.rootOffset }, { id: kind + "-west-" + d, object: west.id, direction: d, x: Math.round(roots[1][0]) - 0.5, y: -Math.round(roots[1][1]) - 0.5, offset: c.rootOffset }, { id: kind + "-north-" + d, object: middle.id, direction: next[d], x: Math.round(roots[2][0]) - 0.5, y: -Math.round(roots[2][1]) - 0.5, offset: c.rootOffset }];
  const ordered = orderPlacements(placements, objects), sprites = ordered.map((p) => {
    const o = objects.find((o2) => o2.id === p.object), f = spriteFrame(o, o.clips[0], p.direction, 0), r = groundRoot(p, o, 128);
    return { x: r[0] - f.root[0], y: r[1] - f.root[1], width: f.frameSize[0], height: f.frameSize[1], rect: f.rect, url: new URL(f.image, location.href).href };
  });
  const bounds = [-origin[0] + c.pan[0], -origin[1] + c.pan[1], ...size], plan = worldRasterPlan(sprites, bounds), raw = document.createElement("canvas");
  paintWorldRaster(raw, plan, await Promise.all(sprites.map((s) => image(s.url))));
  const ref = { x: -origin[0] + c.rootOffset[0], y: -origin[1] + c.rootOffset[1], width: size[0], height: size[1], rect: [0, 0, size[0] * 2, size[1] * 2], url: new URL("../../candidates/round-01/" + kind + "/" + d + ".png", location.href).href };
  const control = document.createElement("canvas"), refPlan = worldRasterPlan([ref], bounds);
  paintWorldRaster(control, refPlan, [await image(ref.url)]);
  window.nativeCanvasPNGs.push({ id: kind + "-" + d + "-independent", png: raw.toDataURL() }, { id: kind + "-" + d + "-native-control", png: control.toDataURL() });
  for (const [bg, color] of [["light", "#eeeeee"], ["gray", "#808080"], ["dark", "#151923"]]) {
    const sec = document.createElement("section");
    sec.id = kind + "-" + d + "-" + bg;
    sec.style.width = size[0] * c.cssScale + "px";
    const label = document.createElement("p");
    label.textContent = kind + " / " + d + " / " + bg;
    sec.append(label);
    const canvas = document.createElement("canvas");
    canvas.width = size[0] * 2;
    canvas.height = size[1] * 2;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(raw, (plan.x - bounds[0]) * 2, (plan.y - bounds[1]) * 2);
    canvas.style.width = size[0] * c.cssScale + "px";
    canvas.style.height = size[1] * c.cssScale + "px";
    sec.append(canvas);
    document.querySelector("#fixture").append(sec);
    window.evidence.fixtures.push({ kind, direction: d, background: bg, color, orderedPlacements: ordered, plan, bounds, referencePlan: refPlan, nativeSize: [raw.width, raw.height], controlSize: [control.width, control.height], displayCSS: [size[0] * c.cssScale, size[1] * c.cssScale], nativeSmoothing: raw.getContext("2d").imageSmoothingEnabled, displayCanvasSmoothing: ctx.imageSmoothingEnabled });
  }
}
window.ready = true;
/*! Bundled license information:

react/cjs/react.production.js:
  (**
   * @license React
   * react.production.js
   *
   * Copyright (c) Meta Platforms, Inc. and affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   *)
*/
