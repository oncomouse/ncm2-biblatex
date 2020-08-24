if get(s:, 'loaded', 0)
  finish
endif
let s:loaded = 1
let g:ncm2_biblatex#enabled = get(g:, 'ncm2_biblatex#enabled',  0)
let g:ncm2_biblatex#mark = get(g:, 'ncm2_biblatex#mark', 'bib')
let g:ncm2_biblatex#scope = get(g:, 'ncm2_biblatex#scope', ['markdown', 'rst'])
let g:ncm2_biblatex#proc = yarp#py3({
      \ 'module': 'ncm2_biblatex',
      \ 'on_load': { -> ncm2#set_ready(g:ncm2_biblatex#source)}
      \ })
"       \ 'word_pattern': '\[(?:[\w,]+:)?(?:@?[\w-]+,)*@?[\w-]+',
let g:ncm2_biblatex#source = get(g:, 'ncm2_biblatex#biblatex_source', {
      \ 'name': 'bib',
      \ 'priority': 8,
      \ 'ready': 0,
      \ 'mark': g:ncm2_biblatex#mark,
      \ 'scope': g:ncm2_biblatex#scope,
      \ 'complete_length': 3,
      \ 'on_complete': 'ncm2_biblatex#on_complete',
      \ 'on_warmup': 'ncm2_biblatex#on_warmup'
      \ })
let g:ncm2_biblatex#source = extend(g:ncm2_biblatex#source,
      \ get(g:, 'ncm2_biblatex#source_override', {}),
      \ 'force')
function! ncm2_biblatex#init() abort
  call ncm2#register_source(g:ncm2_biblatex#source)
endfunction

function! ncm2_biblatex#on_warmup(ctx)
  call g:ncm2_biblatex#proc.try_notify('on_warmup', a:ctx)
endfunction

function! ncm2_biblatex#on_complete(ctx)
  let s:is_enabled = get(b:, 'ncm2_biblatex_enabled',
              \ get(g:, 'ncm2_biblatex#enabled', 0))
  if ! s:is_enabled
    return
  endif
  call g:ncm2_biblatex#proc.try_notify('on_complete', a:ctx)
endfunction
