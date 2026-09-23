// Le frecce mostrano tutti i pezzi. Acquista sblocca, Salva li indossa.
const datiAvatar = JSON.parse(document.getElementById("dati-avatar").textContent);
const editorAvatar = document.getElementById("editor-avatar");
const formAvatar = document.getElementById("form-avatar");
const erroreAvatar = document.getElementById("errore-avatar");
const partiAvatar = ["testa", "corpo", "piedi"];
let sceltaAvatar = {...datiAvatar.scelta};
let operazioneAvatar = false;

function articoloScelto(parte) {
    return datiAvatar.catalogo.find(a => a.parte === parte && a.immagine === sceltaAvatar[parte]);
}

function mostraAvatar() {
    let bloccato = false;
    for (const parte of partiAvatar) {
        const articolo = articoloScelto(parte);
        formAvatar.elements[parte].value = sceltaAvatar[parte];
        document.querySelector('[data-anteprima="' + parte + '"]').src =
            datiAvatar.base + parte + "/" + sceltaAvatar[parte] + ".png?v=2";
        const lucchetto = formAvatar.querySelector('[data-acquista="' + parte + '"]');
        lucchetto.hidden = Boolean(articolo.posseduto);
        lucchetto.querySelector("[data-prezzo]").textContent = articolo.prezzo;
        lucchetto.setAttribute("aria-label", "Acquista " + articolo.nome + ": " + articolo.prezzo + " Nickcoin");
        bloccato ||= !articolo.posseduto;
    }
    formAvatar.querySelectorAll("button").forEach(p => p.disabled = operazioneAvatar);
    document.getElementById("salva-avatar").disabled = operazioneAvatar || bloccato;
    document.getElementById("aiuto-avatar").hidden = !bloccato;
}

function aggiornaEconomiaAvatar(esito) {
    if (esito.catalogo) datiAvatar.catalogo = esito.catalogo;
    if (esito.saldo !== undefined) {
        document.getElementById("saldo-avatar").textContent = esito.saldo;
        document.getElementById("saldo-monete").textContent = esito.saldo;
    }
}

async function leggiRispostaAvatar(risposta) {
    if (risposta.status === 401) {
        window.location.replace("/");
        throw new Error("Accesso scaduto.");
    }
    const esito = await risposta.json();
    aggiornaEconomiaAvatar(esito);
    if (!risposta.ok) throw new Error(esito.errore || "Operazione non riuscita.");
    return esito;
}

document.getElementById("apri-avatar").addEventListener("click", async () => {
    if (operazioneAvatar) return;
    sceltaAvatar = {...datiAvatar.scelta};
    erroreAvatar.textContent = "";
    operazioneAvatar = true;
    mostraAvatar();
    editorAvatar.showModal();
    try {
        await leggiRispostaAvatar(await fetch(datiAvatar.economia, {cache: "no-store"}));
    } catch (errore) {
        erroreAvatar.textContent = errore.message;
    } finally {
        operazioneAvatar = false;
        mostraAvatar();
    }
});
document.getElementById("chiudi-avatar").addEventListener("click", () => editorAvatar.close());

formAvatar.querySelectorAll("[data-passo]").forEach(pulsante => {
    pulsante.addEventListener("click", () => {
        const parte = pulsante.dataset.parte;
        const opzioni = datiAvatar.catalogo.filter(a => a.parte === parte);
        const indice = opzioni.findIndex(a => a.immagine === sceltaAvatar[parte]);
        const prossimo = (indice + Number(pulsante.dataset.passo) + opzioni.length) % opzioni.length;
        sceltaAvatar[parte] = opzioni[prossimo].immagine;
        erroreAvatar.textContent = "";
        mostraAvatar();
    });
});

formAvatar.querySelectorAll("[data-acquista]").forEach(pulsante => {
    pulsante.addEventListener("click", async () => {
        if (operazioneAvatar) return;
        const dati = new FormData();
        dati.set("cosmetico_id", articoloScelto(pulsante.dataset.acquista).id);
        operazioneAvatar = true;
        erroreAvatar.textContent = "";
        mostraAvatar();
        try {
            await leggiRispostaAvatar(await fetch(datiAvatar.acquista, {method: "POST", body: dati}));
        } catch (errore) {
            erroreAvatar.textContent = errore.message;
        } finally {
            operazioneAvatar = false;
            mostraAvatar();
        }
    });
});

formAvatar.addEventListener("submit", async evento => {
    evento.preventDefault();
    if (operazioneAvatar || partiAvatar.some(p => !articoloScelto(p).posseduto)) return;
    operazioneAvatar = true;
    erroreAvatar.textContent = "";
    mostraAvatar();
    try {
        await leggiRispostaAvatar(await fetch(formAvatar.action, {method: "POST", body: new FormData(formAvatar)}));
        datiAvatar.scelta = {...sceltaAvatar};
        for (const parte of partiAvatar) {
            document.querySelector('[data-mini="' + parte + '"]').src =
                datiAvatar.base + parte + "/" + sceltaAvatar[parte] + ".png?v=2";
        }
        editorAvatar.close();
    } catch (errore) {
        erroreAvatar.textContent = errore.message;
    } finally {
        operazioneAvatar = false;
        mostraAvatar();
    }
});
