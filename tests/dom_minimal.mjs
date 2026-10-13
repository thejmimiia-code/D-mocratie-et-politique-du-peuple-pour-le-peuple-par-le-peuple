/**
 * tests/dom_minimal.mjs — un DOM minuscule, écrit ici, pour éprouver le
 * JavaScript de la page en Node, sans navigateur et sans dépendance.
 *
 * Il ne cherche pas à imiter un navigateur : il fournit exactement ce dont les
 * fonctions visées ont besoin (classes, attributs, enfants, ordre du document)
 * et **jette** sur tout le reste, pour qu'une fonction qui s'appuie sur autre
 * chose se voie tout de suite.
 *
 * Sélecteurs gérés : `tag`, `.classe`, `[attribut]`, et les listes séparées
 * par des virgules. C'est tout — et c'est suffisant pour les contrôles.
 */

export class ClassList {
  constructor(element) {
    this.element = element;
    this.valeurs = new Set();
  }
  get valeur() { return [...this.valeurs].join(" "); }
  add(classe) { this.valeurs.add(classe); this.element._classes = this.valeur; }
  remove(classe) { this.valeurs.delete(classe); this.element._classes = this.valeur; }
  contains(classe) { return this.valeurs.has(classe); }
  toggle(classe, force) {
    // Le second argument de `classList.toggle` est standard : sans lui,
    // `toggle(classe, false)` ajoutait la classe au lieu de la retirer, et le
    // contrôle passait sur une doublure qui ne ressemblait plus au navigateur.
    if (force === undefined) {
      if (this.valeurs.has(classe)) { this.remove(classe); return false; }
      this.add(classe);
      return true;
    }
    if (force) { this.add(classe); return true; }
    this.remove(classe);
    return false;
  }
}

export class Element {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.enfants = [];
    this.parentNode = null;
    this.parentElement = null;
    this.attributs = {};
    this.textContent = "";
    this._classes = "";
    this.classList = new ClassList(this);
  }

  get className() { return this._classes; }
  set className(valeur) {
    this._classes = valeur;
    this.classList.valeurs = new Set(String(valeur).split(/\s+/).filter(Boolean));
  }

  /** `hidden` est un attribut, pas un simple drapeau : on le tient synchronisé. */
  get hidden() { return this.hasAttribute("hidden"); }
  set hidden(valeur) {
    if (valeur) this.setAttribute("hidden", "");
    else this.removeAttribute("hidden");
  }

  /** Le style en ligne : seules les propriétés personnalisées sont écrites ici. */
  get style() {
    if (!this._style) {
      this._style = {
        valeurs: {},
        setProperty(nom, valeur) { this.valeurs[nom] = String(valeur); },
        getPropertyValue(nom) {
          return Object.prototype.hasOwnProperty.call(this.valeurs, nom) ? this.valeurs[nom] : "";
        },
      };
    }
    return this._style;
  }

  setAttribute(nom, valeur) { this.attributs[nom] = String(valeur); }
  getAttribute(nom) {
    return Object.prototype.hasOwnProperty.call(this.attributs, nom) ? this.attributs[nom] : null;
  }
  hasAttribute(nom) { return Object.prototype.hasOwnProperty.call(this.attributs, nom); }
  removeAttribute(nom) { delete this.attributs[nom]; }

  appendChild(enfant) {
    if (enfant.parentNode) enfant.parentNode.retirer(enfant);
    enfant.parentNode = this;
    enfant.parentElement = this;
    this.enfants.push(enfant);
    return enfant;
  }

  insertBefore(nouveau, reference) {
    const rang = this.enfants.indexOf(reference);
    nouveau.parentNode = this;
    nouveau.parentElement = this;
    if (rang < 0) this.enfants.push(nouveau);
    else this.enfants.splice(rang, 0, nouveau);
    return nouveau;
  }

  retirer(enfant) {
    const rang = this.enfants.indexOf(enfant);
    if (rang >= 0) this.enfants.splice(rang, 1);
    if (enfant.parentNode === this) { enfant.parentNode = null; enfant.parentElement = null; }
  }

  descendants() {
    return this.enfants.flatMap(enfant => [enfant, ...enfant.descendants()]);
  }

  /** Un morceau simple : `tag`, `.classe`, `[attribut]`, dans n'importe quel ordre. */
  correspondSimple(morceau) {
    let reste = morceau;
    const balise = (reste.match(/^[a-zA-Z][\w-]*/) || [null])[0];
    if (balise) reste = reste.slice(balise.length);
    const attribut = (reste.match(/^\[([\w-]+)\]/) || [null, null])[1];
    const classe = (reste.match(/^\.([\w-]+)/) || [null, null])[1];
    if (balise && this.tagName !== balise.toUpperCase()) return false;
    if (attribut && !this.hasAttribute(attribut)) return false;
    if (classe && !this.classList.contains(classe)) return false;
    return true;
  }

  correspond(selecteur) {
    return String(selecteur).split(",").map(partie => partie.trim()).filter(Boolean).some(brut => {
      const morceaux = brut.split(/\s+/).filter(Boolean);
      if (!morceaux.length) return false;
      // Un sélecteur descendant (« .sommaire a ») se lit de droite à gauche :
      // le dernier morceau décrit l'élément, les précédents ses ancêtres.
      if (!this.correspondSimple(morceaux[morceaux.length - 1])) return false;
      let ancetre = this.parentElement;
      for (let rang = morceaux.length - 2; rang >= 0; rang -= 1) {
        while (ancetre && !ancetre.correspondSimple(morceaux[rang])) ancetre = ancetre.parentElement;
        if (!ancetre) return false;
        ancetre = ancetre.parentElement;
      }
      return true;
    });
  }

  querySelectorAll(selecteur) {
    return this.descendants().filter(noeud => noeud.correspond(selecteur));
  }
}

export class Document {
  constructor() {
    this.body = new Element("body");
    this.racine = this.body;
    this.documentElement = new Element("html");
  }
  createElement(balise) { return new Element(balise); }
  querySelectorAll(selecteur) { return this.racine.querySelectorAll(selecteur); }
  getElementById(identifiant) {
    return this.racine.descendants().find(noeud => noeud.getAttribute("id") === String(identifiant))
      || null;
  }
}
