#!/usr/bin/env python3
"""PANDORA PRESS-INVENTORY Ω v0.1.0. Complemento do PRESSROOM v1.3.0."""
import argparse, csv, datetime, html, importlib.util, json, sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from . import press

def inventory(db,author_id):
    a=db.execute("SELECT id,name,url FROM authors WHERE id=?",(author_id,)).fetchone()
    if not a: raise ValueError("autor não encontrado")
    rows=press.list_records(db,author_id)
    evidence={x["record_id"]:x["n"] for x in db.execute(
        "SELECT e.record_id,COUNT(*) n FROM evidence e JOIN records r ON r.id=e.record_id WHERE r.author_id=? GROUP BY e.record_id",(author_id,))}
    kinds=Counter(); statuses=Counter(); years=Counter(); matrix=defaultdict(Counter)
    timeline=[]
    for r in rows:
        date=r["event_date"] or r["publication_date"]
        year=date[:4] if date else "sem_data"
        kinds[r["kind"]]+=1;statuses[r["status"]]+=1;years[year]+=1;matrix[year][r["kind"]]+=1
        timeline.append({"id":r["id"],"date":date,"kind":r["kind"],"title":r["title"],
                         "status":r["status"],"url":r["url"],"evidence_count":evidence.get(r["id"],0)})
    candidates=Counter(x["status"] for x in db.execute("SELECT status FROM candidates WHERE author_id=?",(author_id,)))
    return {"author":dict(a),"generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_records":len(rows),"by_kind":dict(sorted(kinds.items())),
            "by_status":dict(sorted(statuses.items())),"by_year":dict(sorted(years.items())),
            "by_year_kind":{y:dict(sorted(v.items())) for y,v in sorted(matrix.items())},
            "with_evidence":sum(r["id"] in evidence for r in rows),
            "without_evidence":sum(r["id"] not in evidence for r in rows),
            "total_evidence":sum(evidence.values()),
            "with_primary_url":sum(bool(r["url"]) for r in rows),
            "without_date":sum(not r["date"] for r in timeline),
            "date_precision":dict(sorted(Counter(r["date_precision"] for r in rows).items())),
            "candidates_separate":dict(sorted(candidates.items())),
            "timeline":timeline,
            "methodology":"Conta IDs de registros, não candidatos; não mede impacto, qualidade ou veracidade."}
def export(data,path,fmt):
    if fmt=="json":Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    elif fmt=="csv":
        with open(path,"w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["id","date","kind","title","status","url","evidence_count"])
            w.writeheader();w.writerows(data["timeline"])
    elif fmt=="pdf":
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        styles=getSampleStyleSheet(); esc=html.escape
        story=[Paragraph("INVENTÁRIO AUTORAL",styles["Title"]),
               Paragraph(esc(data["author"]["name"]),styles["Heading2"]),
               Paragraph("Gerado em "+esc(data["generated_at"]),styles["Normal"]),
               Paragraph("Registros: "+str(data["total_records"])+" | Evidências: "+str(data["total_evidence"]),styles["Heading2"]),
               Paragraph("Totais por segmento",styles["Heading2"])]
        rows=[["Categoria","Quantidade"]]+[[k,str(v)] for k,v in data["by_kind"].items()]
        t=Table(rows,colWidths=[10*cm,4*cm]);t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E5ECE9")),("LINEBELOW",(0,0),(-1,-1),.3,colors.grey)]));story.append(t)
        story.append(Paragraph("Distribuição anual",styles["Heading2"]))
        for y,n in data["by_year"].items():story.append(Paragraph(esc(y)+": "+str(n),styles["Normal"]))
        story.append(Paragraph("Estado de verificação",styles["Heading2"]))
        for k,n in data["by_status"].items():story.append(Paragraph(esc(k)+": "+str(n),styles["Normal"]))
        story.append(Paragraph("Candidatos não incluídos nos totais",styles["Heading2"]))
        for k,n in data["candidates_separate"].items():story.append(Paragraph(esc(k)+": "+str(n),styles["Normal"]))
        story.append(Paragraph("Cronologia",styles["Heading2"]))
        for r in data["timeline"]:
            story.append(Paragraph(esc((r["date"] or "Sem data")+" | "+r["kind"]+" | "+r["title"]+" | "+r["status"]),styles["Normal"]))
        story.append(Spacer(1,12));story.append(Paragraph(esc(data["methodology"]),styles["Italic"]))
        SimpleDocTemplate(path,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm).build(story)
def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        db=press.connect(str(Path(d)/"t.db"))
        with db:db.execute("INSERT INTO authors VALUES (?,?,?,?,?)",("a","Autor Teste",None,"",press.now()))
        with db:
            press.save(db,"a",{"title":"Paper recente","kind":"paper","event_date":"2026-02","status":"verified"})
            press.save(db,"a",{"title":"Livro antigo","kind":"book","event_date":"2020","status":"pending"})
            press.save(db,"a",{"title":"Software sem data","kind":"software"})
        data=inventory(db,"a")
        assert data["total_records"]==3 and data["by_kind"]=={"book":1,"paper":1,"software":1}
        assert data["without_date"]==1 and data["timeline"][0]["kind"]=="book"
        assert data["by_status"]["verified"]==1
        assert sum(data["by_year"].values())==3
        export(data,str(Path(d)/"out.csv"),"csv")
        export(data,str(Path(d)/"out.pdf"),"pdf")
        assert Path(d,"out.pdf").stat().st_size>1000
        db.close()
    return {"selftest":"passed","checks":6}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version",action="version",version="0.1.0")
    p.add_argument("--db",default="pressroom.sqlite3")
    s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("inventory");a.add_argument("--author",required=True)
    a.add_argument("--format",choices=["json","csv","pdf"],default="json");a.add_argument("--out")
    s.add_parser("selftest")
    args=p.parse_args()
    if args.cmd=="selftest":print(json.dumps(selftest()));return
    db=press.connect(args.db)
    try:
        data=inventory(db,args.author)
        if args.out:export(data,args.out,args.format);print(json.dumps({"output":args.out,"total_records":data["total_records"]}))
        elif args.format=="json":print(json.dumps(data,ensure_ascii=False,indent=2))
        else:raise ValueError("--out obrigatório para CSV/PDF")
    finally:db.close()
if __name__=="__main__":main()
