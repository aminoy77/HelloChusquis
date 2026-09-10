# JavaScript classes

- In JavaScript, `class A { constructor(x) { this.x = x; } }` bundles state with methods.
- In JavaScript, `extends` plus `super()` inherit; derived constructors must call `super()` before `this`.
- In JavaScript, `#field` declares truly private state invisible outside the class body.
- In JavaScript, `static` methods belong to the class; instance methods live on the prototype.
- In JavaScript, getters/setters (`get x()`) expose computed properties behind attribute syntax.
- In JavaScript, prefer composition and factories when inheritance hierarchies grow past two levels.
- In JavaScript, `instanceof` checks prototype chains but breaks across realms (iframes).
- In JavaScript, class declarations are not hoisted; define before use unlike functions.
- In JavaScript, arrow-function fields auto-bind `this`, handy for callbacks passed to children.
- In JavaScript, `Object.freeze` instances you intend as immutable value objects.
