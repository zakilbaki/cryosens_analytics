

import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
import ipywidgets as widgets
from IPython.display import display, clear_output

console = Console()

def convert_pressures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interface interactive pour convertir les unités de pression.
    Cible les colonnes 'PI' (exclut automatiquement les 'PDI').
    """
    df = df.copy()
    
    # 1. Identification automatique des colonnes PI (et pas PDI)
    target_cols = [c for c in df.columns if c.lower() != "time" and "P_" in c.upper() and "PD_" not in c.upper()]
    
    if not target_cols:
        _warn("Aucune colonne 'PI' détectée pour la conversion.")
        return df

    # 2. Affichage de l'interface de choix
    console.print(Panel(f"[bold]Conversion d'Unités Pression (PI)[/]\nColonnes ciblées : {', '.join(target_cols)}", style="magenta"))
    
    menu_text = "[white]1[/] → Bar\n[white]2[/] → PSI\n[white]3[/] → kPa"
    
    console.print("[bold cyan]Unité d'ENTRÉE (actuelle des données) :[/]")
    console.print(menu_text)
    choice_in = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="1")
    
    console.print("\n[bold green]Unité de SORTIE (voulue pour l'analyse) :[/]")
    console.print(menu_text)
    choice_out = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="1")

    # Mappage des choix
    mapping = {"1": "BAR", "2": "PSI", "3": "KPA"}
    u_in = mapping[choice_in]
    u_out = mapping[choice_out]

    if u_in == u_out:
        _ok("Unités identiques, aucune modification appliquée.")
        return df

    # 3. Logique de conversion (Pivot Bar)
    for col in target_cols:
        
        # Étape A : On convertit l'entrée en Bar
        if u_in == "PSI":
            df[col] = df[col] / 14.5038
        elif u_in == "KPA":
            df[col] = df[col] / 100
            
        # Étape B : On convertit du Bar vers la sortie
        if u_out == "PSI":
            df[col] = df[col] * 14.5038
        elif u_out == "KPA":
            df[col] = df[col] * 100

    _ok(f"Succès : Conversion {u_in} → {u_out} effectuée sur {len(target_cols)} colonnes.")
    return df


def convert_pdi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interface interactive pour convertir les unités de pression différentielle.
    Cible uniquement les colonnes 'PDI'.
    """
    df = df.copy()
    
    # 1. Identification automatique des colonnes PDI
    target_cols = [c for c in df.columns if c.lower() != "time" and "PD_" in c.upper()]
    
    if not target_cols:
        _warn("Aucune colonne 'PD_' détectée pour la conversion.")
        return df

    # 2. Affichage de l'interface de choix
    console.print(Panel(f"[bold]Conversion d'Unités Différentielles (PD_)[/]\nColonnes ciblées : {', '.join(target_cols)}", style="magenta"))
    
    menu_text = "[white]1[/] → milliBar (mbar)\n[white]2[/] → Inches of Water (inH2O)\n[white]3[/] → Pascal (Pa)"
    
    console.print("[bold cyan]Unité d'ENTRÉE (actuelle des données) :[/]")
    console.print(menu_text)
    choice_in = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="1")
    
    console.print("\n[bold green]Unité de SORTIE (voulue pour l'analyse) :[/]")
    console.print(menu_text)
    choice_out = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="1")

    # Mappage des choix
    mapping = {"1": "MBAR", "2": "INH2O", "3": "PA"}
    u_in = mapping[choice_in]
    u_out = mapping[choice_out]

    if u_in == u_out:
        _ok("Unités identiques, aucune modification appliquée.")
        return df

    # 3. Logique de conversion (Pivot mbar)
    for col in target_cols:
        
        # Étape A : On convertit l'entrée en mbar
        if u_in == "INH2O":
            df[col] = df[col] * 2.49089
        elif u_in == "PA":
            df[col] = df[col] / 100
            
        # Étape B : On convertit du mbar vers la sortie
        if u_out == "INH2O":
            df[col] = df[col] / 2.49089
        elif u_out == "PA":
            df[col] = df[col] * 100

    _ok(f"Succès : Conversion {u_in} → {u_out} effectuée sur {len(target_cols)} colonnes.")
    return df



def convert_temperatures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interface interactive pour convertir les unités de température.
    Prend uniquement le DataFrame en entrée.
    """
    df = df.copy()
    
    # 1. Identification automatique des colonnes TI
    target_cols = [c for c in df.columns if c.lower() != "time" and "T_" in c.upper()]
    
    if not target_cols:
        _warn("Aucune colonne 'T_' détectée pour la conversion.")
        return df

    # 2. Affichage de l'interface de choix
    console.print(Panel(f"[bold]Conversion d'Unités[/]\nColonnes ciblées : {', '.join(target_cols)}", style="magenta"))
    
    # ASTUCE : On crée le texte du menu une seule fois pour garantir que les choix sont identiques
    menu_text = "[white]1[/] → Celsius (°C)\n[white]2[/] → Fahrenheit (°F)\n[white]3[/] → Kelvin (K)"
    
    console.print("[bold cyan]Unité d'ENTRÉE (actuelle des données) :[/]")
    console.print(menu_text)
    choice_in = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="2")
    
    console.print("\n[bold green]Unité de SORTIE (voulue pour l'analyse) :[/]")
    console.print(menu_text)
    choice_out = Prompt.ask("Votre choix", choices=["1", "2", "3"], default="1")

    # Mappage des choix - Maintenant parfaitement aligné avec le menu_text
    mapping = {"1": "C", "2": "F", "3": "K"}
    u_in = mapping[choice_in]
    u_out = mapping[choice_out]

    if u_in == u_out:
        _ok("Unités identiques, aucune modification appliquée.")
        return df

    # 3. Logique de conversion (Pivot Celsius - 100% robuste)
    for col in target_cols:
        
        # Étape A : On convertit l'entrée en Celsius
        if u_in == "F":
            df[col] = (df[col] - 32) * 5 / 9
        elif u_in == "K":
            df[col] = df[col] - 273.15
            
        # Étape B : On convertit du Celsius (la valeur modifiée ci-dessus) vers la sortie
        if u_out == "F":
            df[col] = (df[col] * 9 / 5) + 32
        elif u_out == "K":
            df[col] = df[col] + 273.15

    _ok(f"Succès : Conversion {u_in} → {u_out} effectuée sur {len(target_cols)} colonnes.")
    return df
# ─────────────────────────────────────────────────────────────────────────────
# HELPERS VISUELS (MESSAGES ORIGINAUX)
# ─────────────────────────────────────────────────────────────────────────────
def split_df_by_sensor_types(df: pd.DataFrame):
    if "time" not in df.columns:
        raise ValueError("Le DataFrame doit contenir une colonne 'time'")

    t_cols  = ["time"] + [c for c in df.columns if c != "time" and c.upper().startswith("T_")]
    dp_cols = ["time"] + [c for c in df.columns if c != "time" and c.upper().startswith("DP_")]
    p_cols  = ["time"] + [c for c in df.columns if c != "time" and c.upper().startswith("P_") and not c.upper().startswith("DP_")]

    df_t = df[t_cols].copy() if len(t_cols) > 1 else None
    df_dp = df[dp_cols].copy() if len(dp_cols) > 1 else None
    df_p = df[p_cols].copy() if len(p_cols) > 1 else None

    table = Table(title="Split par type de capteur", box=box.SIMPLE_HEAVY)
    table.add_column("Label", style="bold cyan")
    table.add_column("Colonnes", style="white")
    table.add_column("Shape", style="yellow")

    for label, sub_df in [("T_", df_t), ("DP_", df_dp), ("P_", df_p)]:
        if sub_df is not None:
            table.add_row(label, ", ".join([c for c in sub_df.columns if c != "time"]), str(sub_df.shape))

    console.print(table)
    return df_t, df_dp, df_p

def _show_columns_table(df: pd.DataFrame, title: str = "Colonnes disponibles") -> None:
    table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("#",      style="dim cyan",   justify="right", no_wrap=True)
    table.add_column("Nom",    style="bold white",  no_wrap=False)
    table.add_column("Type",   style="yellow",      no_wrap=True)
    table.add_column("NaN %",  style="red",         justify="right", no_wrap=True)
    table.add_column("Aperçu", style="dim",         no_wrap=True)

    for i, col in enumerate(df.columns):
        nan_pct = df[col].isna().mean() * 100
        nan_str = f"{nan_pct:.1f}%" if nan_pct > 0 else "—"
        preview = str(df[col].dropna().iloc[0]) if df[col].dropna().shape[0] > 0 else "∅"
        dtype   = str(df[col].dtype)
        table.add_row(str(i), str(col), dtype, nan_str, preview[:40])

    console.print(table)


def _show_data_preview(df: pd.DataFrame, n_rows: int = 5, title: str = "Aperçu des données") -> None:
    
    if df.empty:
        _warn("Le DataFrame est vide, rien à afficher.")
        return

    max_cols = 10
    cols_to_show = df.columns[:max_cols]
    
    table = Table(
        title=f"[bold cyan]{title}[/] [dim]({len(df)} lignes x {len(df.columns)} col)[/]", 
        box=box.ROUNDED, 
        header_style="bold magenta",
        border_style="dim blue",
        show_lines=True
    )

    # Colonnes normales uniquement
    for col in cols_to_show:
        table.add_column(str(col), justify="center", no_wrap=True)
    
    if len(df.columns) > max_cols:
        table.add_column("...", justify="center")

    # Lignes
    for i in range(min(n_rows, len(df))):
        row_data = [str(val)[:20] for val in df.iloc[i, :max_cols].values]
        if len(df.columns) > max_cols:
            row_data.append("...")
        table.add_row(*row_data)

    console.print(table)

def _ok(msg: str):   console.print(f"[bold green]✔[/]  {msg}")
def _warn(msg: str): console.print(f"[bold yellow]⚠[/]  {msg}")
def _err(msg: str):  console.print(f"[bold red]✘[/]  {msg}")

def _parse_index_list(raw: str, max_idx: int) -> list[int]:
    indices = []
    for token in raw.split(","):
        token = token.strip()
        if "-" in token and not token.startswith("-"):
            parts = token.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                indices.extend(range(int(parts[0]), int(parts[1]) + 1))
        elif token.isdigit():
            indices.append(int(token))
    return [i for i in indices if 0 <= i < max_idx]

# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS DE TRANSFORMATION
# ─────────────────────────────────────────────────────────────────────────────

def crop_top_rows(df: pd.DataFrame, start_row: int) -> pd.DataFrame:
    if not (0 <= start_row < len(df)):
        _warn(f"start_row={start_row} invalide (0–{len(df)-1}), aucune ligne supprimée")
        return df.copy()
    cropped = df.iloc[start_row:].reset_index(drop=True)
    _ok(f"{start_row} lignes supprimées → {len(cropped)} lignes restantes")
    return cropped

def promote_row_to_header(df: pd.DataFrame, row_index: int = 0) -> pd.DataFrame:
    if not (0 <= row_index < len(df)):
        _err(f"row_index={row_index} invalide")
        return df
    new_cols = df.iloc[row_index].fillna("unnamed").astype(str).tolist()
    seen = {}
    deduped = []
    for c in new_cols:
        count = seen.get(c, 0)
        deduped.append(f"{c}.{count}" if count > 0 else c)
        seen[c] = count + 1
    df = df.iloc[row_index + 1:].reset_index(drop=True)
    df.columns = deduped
    _ok(f"Ligne {row_index} promue en en-tête ({len(df.columns)} colonnes)")
    return df

def choose_and_rename_time_column(df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel("[bold]Sélection de la colonne temporelle[/]", style="cyan"))
    _show_columns_table(df)
    while True:
        raw = Prompt.ask("[cyan]Numéro de la colonne temporelle[/]")
        if raw.isdigit() and 0 <= (idx := int(raw)) < len(df.columns): break
        _warn(f"Entrez un entier entre 0 et {len(df.columns) - 1}")
    old_name = df.columns[idx]
    df.rename(columns={old_name: "time"}, inplace=True)
    _ok(f"Colonne '[italic]{old_name}[/italic]' (index {idx}) renommée en 'time'")
    return df

def drop_columns_interactive(df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel("[bold]Suppression de colonnes[/]", style="cyan"))
    _show_columns_table(df)
    raw = Prompt.ask("[cyan]Colonnes à supprimer[/] (indices/noms, vide pour aucune)", default="")
    if not raw.strip():
        _ok("Aucune colonne supprimée")
        return df
    idx_list = _parse_index_list(raw, len(df.columns))
    cols_to_drop = list(dict.fromkeys([df.columns[i] for i in idx_list] + [t.strip() for t in raw.split(",") if t.strip() in df.columns]))
    if not cols_to_drop:
        _warn("Aucun identifiant valide trouvé")
        return df
    console.print(f"[red]Colonnes qui seront supprimées :[/] {cols_to_drop}")
    if Confirm.ask("Confirmer la suppression ?", default=True):
        df.drop(columns=cols_to_drop, inplace=True)
        _ok(f"{len(cols_to_drop)} colonne(s) supprimée(s)")
    return df

# ─────────────────────────────────────────────────────────────────────────────
# TON AFFICHAGE EXACT POUR LE RENOMMAGE
# ─────────────────────────────────────────────────────────────────────────────

def rename_columns_ui(df: pd.DataFrame) -> None:
    header = widgets.HTML(value="""
    <h3>📝 Renommage des colonnes</h3>
    <p>Modifiez les noms à droite. Laissez tel quel si aucun changement n'est nécessaire.</p>

    <div style="
        padding: 12px;
        margin: 10px 0 15px 0;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        background-color: #f6f8fa;
        line-height: 1.6;
    ">
        <b>Règles de renommage :</b><br>
        • La colonne temporelle doit s'appeler : <code>time</code><br>
        • Les capteurs de température doivent commencer par : <code>T_</code><br>
        • Les capteurs de pression doivent commencer par : <code>P_</code><br>
        • Les capteurs de pression différentielle doivent commencer par : <code>DP_</code><br><br>

        <b>Exemples :</b><br>
        <code>time</code><br>
        <code>T_FEED_IN</code><br>
        <code>P_OUTLET</code><br>
        <code>DP_PASS_A</code><br><br>

        <span style="color:#555;">
        Ces préfixes permettent à la boîte à outils de reconnaître automatiquement les familles de capteurs.
        </span>
    </div>
    """)

    rows = []
    text_boxes = {}
    label_layout = widgets.Layout(width='300px')
    input_layout = widgets.Layout(width='300px')

    for col in df.columns:
        label = widgets.Label(value=str(col), layout=label_layout)
        text_box = widgets.Text(value=str(col), layout=input_layout)
        text_boxes[col] = text_box
        rows.append(widgets.HBox([label, widgets.Label(value=" ➡️ "), text_box]))

    button = widgets.Button(
        description="✅ Valider le renommage",
        button_style='success',
        layout=widgets.Layout(width='250px', margin='20px 0 0 0'),
        icon='check'
    )
    output = widgets.Output()

    def on_button_click(b):
        with output:
            clear_output()
            new_names_map = {old: box.value.strip() for old, box in text_boxes.items()}
            nouveaux_noms = list(new_names_map.values())

            if len(nouveaux_noms) != len(set(nouveaux_noms)):
                print("❌ Erreur : Deux colonnes ne peuvent pas avoir le même nom.")
                return

            changes = {k: v for k, v in new_names_map.items() if k != v}

            if not changes:
                print("ℹ️ Aucune modification effectuée.")
            else:
                df.rename(columns=new_names_map, inplace=True)
                print(f"✨ Succès ! {len(changes)} colonne(s) renommée(s).")
                print(f"Nouveaux noms : {list(changes.values())}")

    button.on_click(on_button_click)
    ui_container = widgets.VBox([header] + rows + [button, output])
    display(ui_container)
# ─────────────────────────────────────────────────────────────────────────────
# NETTOYAGE & NaN
# ─────────────────────────────────────────────────────────────────────────────

def convert_columns_to_float(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col != "time":
            df[col] = pd.to_numeric(df[col], errors='coerce')
    _ok("Toutes les colonnes (hors time) converties en float")
    return df

def handle_nans(df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel("[bold]Gestion des NaN[/]", style="cyan"))
    _show_columns_table(df, "État des NaN")
    
    # Stratégie suggérée : Nettoyage auto des colonnes trop vides
    num_cols = [col for col in df.columns if col != "time"]
    threshold = 0.8  # 80% de vide
    
    cols_to_drop = [c for c in num_cols if df[c].isna().mean() > threshold]
    if cols_to_drop:
        _warn(f"Colonnes exclues car trop vides (>80%) : {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)
        num_cols = [c for c in num_cols if c not in cols_to_drop]

    console.print("\n[bold]Stratégies :[/]\n[cyan]1[/] → Supprimer lignes (Risqué : peut tout vider)"
                  "\n[cyan]2[/] → Moyenne\n[cyan]3[/] → Médiane\n[cyan]4[/] → Interpolation (Conseillé)")
    
    c = Prompt.ask("Votre choix", choices=["1","2","3","4"], default="4")
    
    if c == "1":
        before = len(df)
        df = df.dropna(subset=num_cols).reset_index(drop=True)
        _ok(f"Lignes supprimées : {before - len(df)}")
        
    elif c in ["2", "3"]:
        for col in num_cols:
            val = df[col].mean() if c == "2" else df[col].median()
            df[col] = df[col].fillna(val)
        _ok(f"NaN remplacés par la {'moyenne' if c=='2' else 'médiane'}")
        
    elif c == "4":
        # On limite l'interpolation à 5 points consécutifs pour garder un sens physique
        df[num_cols] = df[num_cols].interpolate(method='linear', limit=5, limit_area='inside')
        # On finit les petits NaNs restants par un ffill/bfill très court
        df[num_cols] = df[num_cols].ffill(limit=2).bfill(limit=2)
        _ok("Interpolation linéaire (max 5 pts consécutifs)")
        
    return df
# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE ORCHESTRATEUR
# ─────────────────────────────────────────────────────────────────────────────
def run_preprocessing_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel(
        "[bold white]Pipeline de Preprocessing[/]\n"
        "[dim]Visualisation active après chaque étape.[/]",
        style="bold blue", expand=False
    ))

    # --- Étape 1 : Rogner ---
    console.rule("[bold cyan]Étape 1/6 — Rogner les lignes du haut[/]")
    _show_data_preview(df, title="État AVANT rognage")
    if Confirm.ask("Exécuter : [bold]Rogner les lignes[/] ?", default=True):
        start_row = IntPrompt.ask("Numéro de la première ligne utile", default=0)
        df = crop_top_rows(df, start_row - 1)
        _show_data_preview(df, title="État APRÈS rognage")

    # --- Étape 2 : Promotion ---
    console.rule("[bold cyan]Étape 2/6 — Promouvoir en en-tête[/]")
    if not df.empty:
        console.print(f"[yellow]Ligne 0 actuelle (sera le futur titre) :[/] {df.iloc[0].values.tolist()}")
        if Confirm.ask("Promouvoir la ligne 0 en en-tête ?", default=True):
            df = promote_row_to_header(df, 0)
            _show_data_preview(df, title="État APRÈS promotion")

    # --- Étape 3 : Temps ---
    console.rule("[bold cyan]Étape 3/6 — Choisir la colonne temporelle[/]")
    if Confirm.ask("Exécuter : [bold]Définir la colonne TIME[/] ?", default=True):
        df = choose_and_rename_time_column(df)

        if "time" in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df["time"]):
                df["time"] = pd.to_datetime(df["time"], errors="coerce")
                _ok("Colonne 'time' convertie en datetime.")
            else:
                _ok("Colonne 'time' déjà au format datetime.")

        _ok("Colonne 'time' configurée.")

    # --- Étape 4 : Suppression ---
    console.rule("[bold cyan]Étape 4/6 — Supprimer des colonnes[/]")
    if Confirm.ask("Exécuter : [bold]Suppression interactive[/] ?", default=True):
        df = drop_columns_interactive(df)
        _show_columns_table(df, "Colonnes restantes")

    # --- Étape 5 : Conversion Float ---
    console.rule("[bold cyan]Étape 5/6 — Convertir les colonnes en float[/]")
    if Confirm.ask("Exécuter : [bold]Conversion Float[/] ?", default=True):
        df = convert_columns_to_float(df)

    # --- Étape 6 : Gestion NaN ---
    console.rule("[bold cyan]Étape 6/6 — Gérer les NaN[/]")

    nan_ratio = df.isna().mean() * 100
    has_nans = (nan_ratio > 0).any()

    if not has_nans:
        _ok("Aucun NaN détecté.")
        _show_data_preview(df, title="Dataset Final Nettoyé")
        return df

    _show_columns_table(df, "Résumé des NaN détectés")

    # Sous-étape A : suppression des colonnes trop vides
    if Confirm.ask("Supprimer les colonnes avec beaucoup de NaN ?", default=True):
        threshold_pct = IntPrompt.ask(
            "Seuil (%) au-dessus duquel une colonne est supprimée",
            default=50
        )

        cols_to_drop = nan_ratio[nan_ratio >= threshold_pct].index.tolist()

        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            _ok(f"Colonnes supprimées : {cols_to_drop}")
            _show_columns_table(df, "Colonnes restantes après suppression NaN")
        else:
            console.print("[yellow]Aucune colonne au-dessus du seuil.[/]")

    remaining_nans = int(df.isna().sum().sum())

    if remaining_nans == 0:
        _ok("Il ne reste plus de NaN après suppression des colonnes.")
        _show_data_preview(df, title="Dataset Final Nettoyé")
        return df

    # Sous-étape B : traitement complémentaire optionnel
    if Confirm.ask("Appliquer ensuite le traitement complémentaire des NaN ?", default=False):
        df = handle_nans(df)
        _show_data_preview(df, title="Dataset Final Nettoyé")
    else:
        _ok("Aucun traitement complémentaire des NaN appliqué.")
        _show_data_preview(df, title="Dataset après gestion simple des NaN")

    return df