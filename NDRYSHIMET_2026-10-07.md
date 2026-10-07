# DataPOS – resetimi, arka dhe raportet

## Çfarë u ndryshua

- Resetimi ditor dhe mujor fshin në server shitjet e periudhës vetëm për firmën e administratorit; nuk është vetëm ndryshim vizual. Shitjet e reja pas resetimit numërohen normalisht.
- Backup-i ruhet PARA fshirjes. Nëse ruajtja e backup-it dështon, shitjet nuk fshihen.
- Reseto Muajin (0) është vendosur poshtë Reseto Ditën (0), me verifikim fjalëkalimi dhe konfirmim.
- Resetimi mbyll/fshin arkat e periudhës dhe arkat ende të hapura, edhe nëse janë hapur më herët. Pas resetimit hapeni arkën përsëri. Gjendja e stokut nuk rikthehet nga resetimi.
- Cache-i lokal i shitjeve/arkës pastrohet pas resetimit dhe fshirjes. Resetimi ndalohet nëse pajisja ka veprime offline ende të pasinkronizuara. Sinkronizoni të gjitha pajisjet para resetimit.
- Te arka: F2 hap pagesën. Shkruani shumën e paguar. Kur kuponi nuk shtypet, Enter-i i parë shfaq “Dëshironi të përfundoni shitjen?”. Enter-i i dytë e dërgon shitjen. Mbajtja shtypur e Enter-it dhe klikimet gjatë kërkesës nuk nisin kërkesa të dyfishta.
- F10 tani hap pagesën me bankë pa auto-submit me gjendje të vjetër; përfundoni me Enter/konfirmim.
- Raportet kanë butonin “Shfaq shitjet e ditës së sotme”, datat e shkruajtshme Nga/Deri dhe listën e shitjeve me faqe prej 50 rreshtash.
- Administratori i firmës mund të zgjedhë “Fshij këtë shitje”. Pas konfirmimit ajo hiqet nga koleksioni aktiv në server, nga raportet dhe nga totalet; një kopje ruhet te deleted_sales për auditim.
- Fshirja nga raportet NUK është kthim malli dhe nuk e shton stokun. Për shitjet pa borxh përditësohet edhe bilanci i pritur i arkës.
- Fshirja nuk vendoset në radhën offline: pa server shfaqet gabim, jo sukses i rremë.
- Raportet, dashboard-i, eksportet dhe resetimi përdorin të njëjtët kufij kalendarikë lokalë. Data e fundit përfshihet plotësisht.

## Instalimi / publikimi

1. Bëni backup të MongoDB-së para publikimit dhe provoni fillimisht në staging.
2. Publikoni backend-in DHE frontend-in e këtij versioni. Vetëm njëri nuk mjafton.
3. Backend përdor BUSINESS_TIMEZONE=Europe/Tirane si parazgjedhje. Mund të vendosni p.sh. Europe/Budapest sipas zonës së biznesit. Timestamp-et vazhdojnë të ruhen në UTC. Kjo zonë është globale për këtë instalim, jo e veçantë për çdo firmë.
4. Nuk kërkohet migrim i shitjeve; koleksioni deleted_sales krijohet në fshirjen e parë.
5. Në mjedisin tuaj me internet instaloni varësitë sipas lockfile-ve ekzistuese dhe ndërtoni frontend-in. Mos përdorni dosjen node_modules të një versioni tjetër.
6. Në një firmë test: bëni shitje, resetoni ditën, rifreskoni; shuma duhet të mbetet 0 deri në shitjen e re. Provoni resetimin mujor, F2/Enter/Enter, filtrimin në një datë dhe fshirjen me refresh. Verifikoni që firma tjetër nuk preket.

## Testet e kryera

- 14 teste backend kaluan, duke përdorur trupat realë të funksioneve dhe një bazë të simuluar në memorie (jo MongoDB prodhimi).
- 7 kontrolle JavaScript kaluan: konfirmimi me dy Enter, mbrojtja nga përsëritja, pagesa e pamjaftueshme, pagesa bankare, dështimi i kërkesës, pastrimi i cache-it dhe mosvendosja e fshirjes në offline queue.
- U analizua sintaksa e 84 skedarëve JS/JSX dhe u kompilua sintaksa Python.
- U kontrolluan pamje të izoluara të kontrolleve të reja me komponentë të thjeshtuar; kjo nuk është test end-to-end i aplikacionit të plotë.
- Build-i i plotë, integrimi me MongoDB dhe prova në domain-in real NUK u kryen. Instalimet npm/pip u bllokuan nga mungesa e aksesit të rrjetit/DNS. Nuk është bërë deploy.

Komandat:

```bash
python3 -m unittest discover -s backend/tests -p test_sales_reset_regressions.py -v
node tests/test_pos_regressions.cjs
```

Testi JavaScript kërkon @babel/parser, i përfshirë në toolchain-in e frontend-it; nëse Node nuk e zgjidh nga rrënja, ekzekutojeni me NODE_PATH të frontend/node_modules.

## Git / push

Arkiva hyrëse nuk kishte .git ose remote. U inicializua një repository lokal dhe u krijuan commit për bazën dhe për ndryshimet. Paketa përmban datapos-history.bundle dhe datapos-fixes.patch.

Push-i nuk u krye: mungon adresa e repository-t dhe lidhja origin. Mos bëni force-push në një repository ekzistues.

Për repository-n tuaj ekzistues mund të aplikoni patch-in mbi të njëjtin version bazë:

```bash
git apply --check /rruga/datapos-fixes.patch
git apply /rruga/datapos-fixes.patch
git add .
git commit -m "Fix persistent daily/monthly resets, POS confirmation and sales reports"
git push origin EMRI_I_DEGES
```

Ose, për të rikrijuar repository-n lokal të paketës:

```bash
git clone datapos-history.bundle datapos-fixed
```

## Kujdes i rëndësishëm për publikim

Në kodin origjinal ekzistojnë endpoint-e init/super-admin që mund të ndryshojnë kredencialet pa autentikim. Kjo dobësi nuk është pjesë e ndryshimeve të kërkuara këtu: çaktivizojini ose mbrojini para publikimit në prodhim. Shmangni testet ekzistuese që lidhen me një server real dhe mund të fshijnë të dhëna; përdorni testet e reja offline të listuara më sipër.
